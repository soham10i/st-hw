"""
STF Digital Twin - Main Controller with Command Queue Architecture

This controller implements the "Global Controller" pattern:
    User (UI) -> API (Queue) -> Controller (Poll) -> MQTT (Execute) -> Hardware (Physics)

The controller polls the database for PENDING commands and executes them sequentially,
ensuring proper coordination between subsystems and preventing race conditions.
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Optional, Dict, List

import httpx

# Optional MQTT support
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("Warning: paho-mqtt not installed. MQTT features disabled.")

# Configuration
API_URL = os.environ.get("STF_API_URL", "http://localhost:8000")
MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
POLL_INTERVAL = float(os.environ.get("POLL_INTERVAL", "1.0"))  # seconds

# Coordinate mapping (slot name -> physical X/Y in mm)
SLOT_COORDINATES = {
    "A1": (100, 100), "A2": (200, 100), "A3": (300, 100),
    "B1": (100, 200), "B2": (200, 200), "B3": (300, 200),
    "C1": (100, 300), "C2": (200, 300), "C3": (300, 300),
}

# Zone coordinates
ZONES = {
    "PICKUP": (25, 25),       # Cookie pickup zone
    "CONVEYOR": (350, 200),   # Conveyor handoff zone
    "OVEN": (350, 100),       # Oven zone
    "HOME": (0, 0),           # Home position
}


class ControllerState(Enum):
    """Finite State Machine states for the controller."""
    IDLE = auto()
    POLLING = auto()
    EXECUTING = auto()
    MOVING_TO_SLOT = auto()
    PICKING = auto()
    MOVING_TO_CONVEYOR = auto()
    PLACING = auto()
    WAITING_OVEN = auto()
    RETURNING = auto()
    ERROR = auto()
    EMERGENCY_STOP = auto()


@dataclass
class HardwarePosition:
    """Tracks the current position and status of a hardware device."""
    device_id: str
    x: float
    y: float
    z: float
    status: str


@dataclass
class QueuedCommand:
    """Represents a command from the database queue."""
    id: int
    command_type: str
    target_slot: Optional[str]
    payload: dict
    status: str
    created_at: datetime


class MainController:
    """
    Main Controller for the STF Digital Twin.
    
    Implements the Command Queue architecture where:
    1. API endpoints create commands with status='PENDING'
    2. Controller polls for PENDING commands
    3. Commands are executed sequentially
    4. Status is updated to 'COMPLETED' or 'FAILED'
    
    Attributes
    ----------
    state : ControllerState
        Current FSM state of the controller.
    http_client : httpx.AsyncClient
        Async HTTP client for API communication.
    mqtt_client : mqtt.Client
        MQTT client for hardware communication.
    running : bool
        Flag indicating if the controller loop is running.
    """
    
    def __init__(self):
        self.state = ControllerState.IDLE
        self.current_command: Optional[QueuedCommand] = None
        self.hardware_positions: Dict[str, HardwarePosition] = {}
        self.mqtt_client: Optional[mqtt.Client] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self.running = False
        
        # Safety flags
        self.emergency_stop_active = False
        
        # Energy tracking
        self.total_energy_joules = 0.0
        self.command_start_time: Optional[float] = None
    
    # =========================================================================
    # MQTT Setup and Handlers
    # =========================================================================
    
    def setup_mqtt(self):
        """Initialize MQTT client for hardware communication."""
        if not MQTT_AVAILABLE:
            print("[Controller] MQTT not available - running in simulation mode")
            return
        
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="stf_controller")
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._on_mqtt_message
        
        try:
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            print(f"[Controller] Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        except Exception as e:
            print(f"[Controller] MQTT connection failed: {e}")
            self.mqtt_client = None
    
    def _on_mqtt_connect(self, client, userdata, flags, reason_code, properties=None):
        """Handle MQTT connection and subscribe to topics."""
        if reason_code == 0 or str(reason_code) == "Success":
            topics = [
                "stf/hbw/status",
                "stf/vgr/status", 
                "stf/conveyor/status",
                "stf/global/emergency",
            ]
            for topic in topics:
                client.subscribe(topic)
            print("[Controller] Subscribed to hardware status topics")
    
    def _on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages from hardware."""
        try:
            payload = json.loads(msg.payload.decode())
            topic = msg.topic
            
            if "/status" in topic:
                self._update_hardware_position(payload)
            elif "emergency" in topic:
                self._handle_emergency_stop()
                
        except json.JSONDecodeError:
            print(f"[Controller] Invalid JSON in MQTT message")
        except Exception as e:
            print(f"[Controller] Error handling MQTT message: {e}")
    
    def _update_hardware_position(self, payload: dict):
        """Update tracked hardware position from MQTT status."""
        device_id = payload.get("device_id")
        if device_id:
            self.hardware_positions[device_id] = HardwarePosition(
                device_id=device_id,
                x=payload.get("x", 0),
                y=payload.get("y", 0),
                z=payload.get("z", 0),
                status=payload.get("status", "UNKNOWN"),
            )
    
    def _handle_emergency_stop(self):
        """Activate emergency stop mode."""
        self.emergency_stop_active = True
        self.state = ControllerState.EMERGENCY_STOP
        
        if self.mqtt_client:
            for device in ["hbw", "vgr", "conveyor"]:
                self.mqtt_client.publish(f"stf/{device}/cmd/stop", json.dumps({"action": "stop"}))
        
        print("[Controller] *** EMERGENCY STOP ACTIVATED ***")
    
    # =========================================================================
    # Hardware Command Methods
    # =========================================================================
    
    async def _send_move_command(self, device_id: str, x: float, y: float) -> bool:
        """
        Send move command to hardware via MQTT and API.
        
        Parameters
        ----------
        device_id : str
            Target device (e.g., 'HBW', 'VGR').
        x : float
            Target X position in mm.
        y : float
            Target Y position in mm.
        
        Returns
        -------
        bool
            True if command was sent successfully.
        """
        # Update API
        try:
            await self.http_client.post(
                f"{API_URL}/hardware/state",
                json={"device_id": device_id, "x": x, "y": y, "z": 0, "status": "MOVING"}
            )
        except Exception as e:
            print(f"[Controller] API update error: {e}")
        
        # Send MQTT command
        if self.mqtt_client:
            topic = f"stf/{device_id.lower()}/cmd/move"
            payload = {"targetX": x, "targetY": y}
            self.mqtt_client.publish(topic, json.dumps(payload))
        
        print(f"[Controller] MOVE {device_id} -> ({x}, {y})")
        return True
    
    async def _send_gripper_command(self, device_id: str, action: str):
        """Send gripper command (open/close/extend/retract)."""
        if self.mqtt_client:
            topic = f"stf/{device_id.lower()}/cmd/gripper"
            payload = {"action": action}
            self.mqtt_client.publish(topic, json.dumps(payload))
        
        print(f"[Controller] GRIPPER {device_id} -> {action}")
    
    async def _send_conveyor_command(self, action: str, speed: float = 100):
        """Send conveyor belt command."""
        if self.mqtt_client:
            topic = "stf/conveyor/cmd/belt"
            payload = {"action": action, "speed": speed}
            self.mqtt_client.publish(topic, json.dumps(payload))
        
        print(f"[Controller] CONVEYOR -> {action}")
    
    async def _wait_for_idle(self, device_id: str, timeout: float = 30.0) -> bool:
        """
        Wait for a device to return to IDLE status.
        
        Parameters
        ----------
        device_id : str
            Device to wait for.
        timeout : float
            Maximum wait time in seconds.
        
        Returns
        -------
        bool
            True if device is IDLE, False if timeout.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check API for current status
            try:
                response = await self.http_client.get(f"{API_URL}/hardware/states")
                if response.status_code == 200:
                    states = response.json()
                    for hw in states:
                        if hw["device_id"] == device_id and hw["status"] == "IDLE":
                            return True
            except Exception:
                pass
            
            await asyncio.sleep(0.5)
        
        print(f"[Controller] Timeout waiting for {device_id} to be IDLE")
        return False
    
    # =========================================================================
    # Command Queue Polling
    # =========================================================================
    
    async def _poll_pending_commands(self) -> Optional[QueuedCommand]:
        """
        Poll the database for the oldest PENDING command.
        
        Returns
        -------
        Optional[QueuedCommand]
            The next command to execute, or None if queue is empty.
        """
        try:
            # Query API for pending commands
            response = await self.http_client.get(
                f"{API_URL}/commands/pending",
                params={"limit": 1}
            )
            
            if response.status_code == 200:
                commands = response.json()
                if commands and len(commands) > 0:
                    cmd = commands[0]
                    return QueuedCommand(
                        id=cmd["id"],
                        command_type=cmd["command_type"],
                        target_slot=cmd.get("target_slot"),
                        payload=json.loads(cmd.get("payload_json", "{}")),
                        status=cmd["status"],
                        created_at=datetime.fromisoformat(cmd["created_at"].replace("Z", "+00:00")),
                    )
            elif response.status_code == 404:
                # Endpoint doesn't exist yet - use dashboard data
                pass
                
        except Exception as e:
            print(f"[Controller] Error polling commands: {e}")
        
        return None
    
    async def _update_command_status(self, command_id: int, status: str, message: str = ""):
        """Update command status in the database."""
        try:
            await self.http_client.post(
                f"{API_URL}/commands/{command_id}/status",
                json={"status": status, "message": message}
            )
        except Exception as e:
            print(f"[Controller] Error updating command status: {e}")
    
    # =========================================================================
    # Command Execution - Process Order
    # =========================================================================
    
    async def _execute_process_command(self, cmd: QueuedCommand):
        """
        Execute a PROCESS command (RAW_DOUGH -> BAKED).
        
        Workflow:
        1. Move HBW to source slot
        2. Pick up cookie
        3. Move to conveyor
        4. Place on conveyor
        5. Start conveyor (simulates oven)
        6. Wait for baking
        7. Pick from conveyor
        8. Return to slot
        """
        slot_name = cmd.target_slot
        if not slot_name or slot_name not in SLOT_COORDINATES:
            print(f"[Controller] Invalid slot: {slot_name}")
            return False
        
        target_x, target_y = SLOT_COORDINATES[slot_name]
        self.command_start_time = time.time()
        
        try:
            # Step 1: Move to slot
            self.state = ControllerState.MOVING_TO_SLOT
            print(f"[Controller] Step 1: Moving to slot {slot_name}")
            await self._send_move_command("HBW", target_x, target_y)
            await asyncio.sleep(2.0)  # Simulated movement time
            await self._wait_for_idle("HBW", timeout=10)
            
            # Step 2: Pick up cookie
            self.state = ControllerState.PICKING
            print(f"[Controller] Step 2: Picking cookie from {slot_name}")
            await self._send_gripper_command("HBW", "extend")
            await asyncio.sleep(0.5)
            await self._send_gripper_command("HBW", "close")
            await asyncio.sleep(0.5)
            await self._send_gripper_command("HBW", "retract")
            await asyncio.sleep(0.5)
            
            # Step 3: Move to conveyor
            self.state = ControllerState.MOVING_TO_CONVEYOR
            print(f"[Controller] Step 3: Moving to conveyor")
            conv_x, conv_y = ZONES["CONVEYOR"]
            await self._send_move_command("HBW", conv_x, conv_y)
            await asyncio.sleep(2.0)
            await self._wait_for_idle("HBW", timeout=10)
            
            # Step 4: Place on conveyor
            self.state = ControllerState.PLACING
            print(f"[Controller] Step 4: Placing on conveyor")
            await self._send_gripper_command("HBW", "extend")
            await asyncio.sleep(0.5)
            await self._send_gripper_command("HBW", "open")
            await asyncio.sleep(0.5)
            await self._send_gripper_command("HBW", "retract")
            await asyncio.sleep(0.5)
            
            # Step 5: Start conveyor (oven simulation)
            self.state = ControllerState.WAITING_OVEN
            print(f"[Controller] Step 5: Starting oven cycle")
            await self._send_conveyor_command("start")
            await asyncio.sleep(3.0)  # Simulated baking time
            await self._send_conveyor_command("stop")
            
            # Step 6: Pick from conveyor
            print(f"[Controller] Step 6: Picking baked cookie")
            await self._send_gripper_command("HBW", "extend")
            await asyncio.sleep(0.5)
            await self._send_gripper_command("HBW", "close")
            await asyncio.sleep(0.5)
            await self._send_gripper_command("HBW", "retract")
            await asyncio.sleep(0.5)
            
            # Step 7: Return to slot
            self.state = ControllerState.RETURNING
            print(f"[Controller] Step 7: Returning to slot {slot_name}")
            await self._send_move_command("HBW", target_x, target_y)
            await asyncio.sleep(2.0)
            await self._wait_for_idle("HBW", timeout=10)
            
            # Step 8: Place cookie
            print(f"[Controller] Step 8: Placing baked cookie")
            await self._send_gripper_command("HBW", "extend")
            await asyncio.sleep(0.5)
            await self._send_gripper_command("HBW", "open")
            await asyncio.sleep(0.5)
            await self._send_gripper_command("HBW", "retract")
            await asyncio.sleep(0.5)
            
            # Log energy consumption
            elapsed_time = time.time() - self.command_start_time
            energy_joules = 24.0 * 1.5 * elapsed_time  # V * A * s
            await self._log_energy(energy_joules, elapsed_time)
            
            print(f"[Controller] PROCESS complete for {slot_name} ({elapsed_time:.1f}s, {energy_joules:.1f}J)")
            return True
            
        except Exception as e:
            print(f"[Controller] Error executing PROCESS: {e}")
            return False
    
    async def _execute_store_command(self, cmd: QueuedCommand):
        """Execute a STORE command."""
        slot_name = cmd.target_slot
        if not slot_name or slot_name not in SLOT_COORDINATES:
            print(f"[Controller] Invalid slot: {slot_name}")
            return False
        
        target_x, target_y = SLOT_COORDINATES[slot_name]
        self.command_start_time = time.time()
        
        try:
            # Move to pickup
            print(f"[Controller] STORE: Moving to pickup zone")
            pickup_x, pickup_y = ZONES["PICKUP"]
            await self._send_move_command("HBW", pickup_x, pickup_y)
            await asyncio.sleep(1.5)
            
            # Pick
            await self._send_gripper_command("HBW", "close")
            await asyncio.sleep(0.5)
            
            # Move to slot
            print(f"[Controller] STORE: Moving to slot {slot_name}")
            await self._send_move_command("HBW", target_x, target_y)
            await asyncio.sleep(2.0)
            
            # Place
            await self._send_gripper_command("HBW", "open")
            await asyncio.sleep(0.5)
            
            elapsed_time = time.time() - self.command_start_time
            energy_joules = 24.0 * 1.2 * elapsed_time
            await self._log_energy(energy_joules, elapsed_time)
            
            print(f"[Controller] STORE complete for {slot_name}")
            return True
            
        except Exception as e:
            print(f"[Controller] Error executing STORE: {e}")
            return False
    
    async def _execute_retrieve_command(self, cmd: QueuedCommand):
        """Execute a RETRIEVE command."""
        slot_name = cmd.target_slot
        if not slot_name or slot_name not in SLOT_COORDINATES:
            print(f"[Controller] Invalid slot: {slot_name}")
            return False
        
        target_x, target_y = SLOT_COORDINATES[slot_name]
        self.command_start_time = time.time()
        
        try:
            # Move to slot
            print(f"[Controller] RETRIEVE: Moving to slot {slot_name}")
            await self._send_move_command("HBW", target_x, target_y)
            await asyncio.sleep(2.0)
            
            # Pick
            await self._send_gripper_command("HBW", "close")
            await asyncio.sleep(0.5)
            
            # Move to dropoff
            print(f"[Controller] RETRIEVE: Moving to dropoff zone")
            await self._send_move_command("HBW", 375, 375)
            await asyncio.sleep(2.0)
            
            # Release
            await self._send_gripper_command("HBW", "open")
            await asyncio.sleep(0.5)
            
            elapsed_time = time.time() - self.command_start_time
            energy_joules = 24.0 * 1.2 * elapsed_time
            await self._log_energy(energy_joules, elapsed_time)
            
            print(f"[Controller] RETRIEVE complete for {slot_name}")
            return True
            
        except Exception as e:
            print(f"[Controller] Error executing RETRIEVE: {e}")
            return False
    
    async def _log_energy(self, joules: float, duration_sec: float):
        """Log energy consumption to API."""
        try:
            await self.http_client.post(
                f"{API_URL}/energy",
                json={
                    "device_id": "HBW",
                    "joules": joules,
                    "voltage": 24.0,
                    "current_amps": joules / (24.0 * duration_sec) if duration_sec > 0 else 0,
                    "power_watts": joules / duration_sec if duration_sec > 0 else 0,
                }
            )
        except Exception as e:
            print(f"[Controller] Energy log error: {e}")
    
    # =========================================================================
    # Main Control Loop
    # =========================================================================
    
    async def run(self):
        """
        Main controller loop implementing the Command Queue pattern.
        
        Loop Steps:
        1. Poll for PENDING commands
        2. Execute command (if found)
        3. Update command status
        4. Repeat
        """
        self.running = True
        self.setup_mqtt()
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            self.http_client = client
            
            print("=" * 60)
            print("STF Digital Twin - Command Queue Controller")
            print("=" * 60)
            print(f"API URL: {API_URL}")
            print(f"Poll Interval: {POLL_INTERVAL}s")
            print("=" * 60)
            
            while self.running:
                try:
                    if self.emergency_stop_active:
                        print("[Controller] Emergency stop active - waiting for reset")
                        await asyncio.sleep(5.0)
                        continue
                    
                    # Poll for pending commands
                    self.state = ControllerState.POLLING
                    cmd = await self._poll_pending_commands()
                    
                    if cmd:
                        print(f"\n[Controller] Processing command #{cmd.id}: {cmd.command_type}")
                        self.current_command = cmd
                        self.state = ControllerState.EXECUTING
                        
                        # Update status to IN_PROGRESS
                        await self._update_command_status(cmd.id, "IN_PROGRESS")
                        
                        # Execute based on command type
                        success = False
                        if cmd.command_type == "PROCESS":
                            success = await self._execute_process_command(cmd)
                        elif cmd.command_type == "STORE":
                            success = await self._execute_store_command(cmd)
                        elif cmd.command_type == "RETRIEVE":
                            success = await self._execute_retrieve_command(cmd)
                        else:
                            print(f"[Controller] Unknown command type: {cmd.command_type}")
                        
                        # Update final status
                        final_status = "COMPLETED" if success else "FAILED"
                        await self._update_command_status(cmd.id, final_status)
                        
                        self.current_command = None
                    
                    # Return to idle
                    self.state = ControllerState.IDLE
                    await asyncio.sleep(POLL_INTERVAL)
                    
                except Exception as e:
                    print(f"[Controller] Error in main loop: {e}")
                    self.state = ControllerState.ERROR
                    await asyncio.sleep(2.0)
        
        # Cleanup
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        
        print("[Controller] Shutdown complete")
    
    def stop(self):
        """Stop the controller gracefully."""
        self.running = False


async def main():
    """Entry point for the controller."""
    controller = MainController()
    
    try:
        await controller.run()
    except KeyboardInterrupt:
        print("\n[Controller] Interrupted by user")
        controller.stop()


if __name__ == "__main__":
    asyncio.run(main())
