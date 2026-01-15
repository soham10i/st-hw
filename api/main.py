"""
STF Digital Twin - FastAPI REST API
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    get_db, init_database, Carrier, Cookie, CookieFlavor, CookieStatus,
    InventorySlot, HardwareState, HardwareStatus, SystemLog, LogLevel,
    EnergyLog, TelemetryHistory, Alert, AlertSeverity, Command,
    get_slot_coordinates, seed_inventory_slots, seed_hardware_devices,
)

app = FastAPI(
    title="STF Digital Twin API",
    description="REST API for the Smart Tabletop Factory Digital Twin",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class HardwareStateUpdate(BaseModel):
    device_id: str
    x: float
    y: float
    z: float = 0.0
    status: Optional[str] = None

class HardwareStateResponse(BaseModel):
    device_id: str
    current_x: float
    current_y: float
    current_z: float
    status: str
    updated_at: datetime
    class Config:
        from_attributes = True

class TelemetryData(BaseModel):
    device_id: str
    metric_name: str
    metric_value: float
    unit: Optional[str] = None

class EnergyData(BaseModel):
    device_id: str
    joules: float
    voltage: float = 24.0

class InventorySlotResponse(BaseModel):
    slot_name: str
    x_pos: int
    y_pos: int
    carrier_id: Optional[int]
    cookie_flavor: Optional[str]
    cookie_status: Optional[str]
    class Config:
        from_attributes = True

class SystemLogResponse(BaseModel):
    id: int
    timestamp: datetime
    level: str
    source: Optional[str]
    message: str
    class Config:
        from_attributes = True

class EnergyStatsResponse(BaseModel):
    total_joules: float
    total_kwh: float
    devices: dict

class DashboardDataResponse(BaseModel):
    inventory: List[InventorySlotResponse]
    hardware: List[HardwareStateResponse]
    logs: List[SystemLogResponse]
    energy: EnergyStatsResponse
    stats: dict

class StoreRequest(BaseModel):
    slot_name: Optional[str] = None
    flavor: str = "CHOCO"

class RetrieveRequest(BaseModel):
    slot_name: str

class CommandResponse(BaseModel):
    success: bool
    message: str
    command_id: Optional[int] = None
    slot_name: Optional[str] = None
    batch_uuid: Optional[str] = None

# Startup
@app.on_event("startup")
async def startup_event():
    try:
        init_database(seed_data=True)
        print("STF Digital Twin API started")
    except Exception as e:
        print(f"Database init warning: {e}")

# Hardware Endpoints
@app.post("/hardware/state", response_model=HardwareStateResponse, tags=["Hardware"])
def update_hardware_state(data: HardwareStateUpdate, db: Session = Depends(get_db)):
    hw = db.query(HardwareState).filter(HardwareState.device_id == data.device_id).first()
    if not hw:
        hw = HardwareState(
            device_id=data.device_id,
            current_x=data.x, current_y=data.y, current_z=data.z,
            status=HardwareStatus[data.status] if data.status else HardwareStatus.IDLE,
        )
        db.add(hw)
    else:
        hw.current_x = data.x
        hw.current_y = data.y
        hw.current_z = data.z
        if data.status:
            hw.status = HardwareStatus[data.status]
        hw.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(hw)
    return HardwareStateResponse(
        device_id=hw.device_id, current_x=hw.current_x, current_y=hw.current_y,
        current_z=hw.current_z, status=hw.status.value, updated_at=hw.updated_at,
    )

@app.get("/hardware/states", response_model=List[HardwareStateResponse], tags=["Hardware"])
def get_all_hardware_states(db: Session = Depends(get_db)):
    devices = db.query(HardwareState).all()
    return [
        HardwareStateResponse(
            device_id=hw.device_id, current_x=hw.current_x, current_y=hw.current_y,
            current_z=hw.current_z, status=hw.status.value, updated_at=hw.updated_at,
        ) for hw in devices
    ]

# Telemetry Endpoints
@app.post("/telemetry", tags=["Telemetry"])
def record_telemetry(data: TelemetryData, db: Session = Depends(get_db)):
    telemetry = TelemetryHistory(
        device_id=data.device_id, metric_name=data.metric_name,
        metric_value=data.metric_value, unit=data.unit,
    )
    db.add(telemetry)
    db.commit()
    return {"success": True, "id": telemetry.id}

# Energy Endpoints
@app.post("/energy", tags=["Energy"])
def record_energy(data: EnergyData, db: Session = Depends(get_db)):
    energy = EnergyLog(device_id=data.device_id, joules=data.joules, voltage=data.voltage)
    db.add(energy)
    db.commit()
    return {"success": True, "id": energy.id}

# Inventory Endpoints
@app.get("/inventory", response_model=List[InventorySlotResponse], tags=["Inventory"])
def get_inventory(db: Session = Depends(get_db)):
    slots = db.query(InventorySlot).all()
    result = []
    for slot in slots:
        cookie_flavor, cookie_status = None, None
        if slot.carrier_id:
            carrier = db.query(Carrier).filter(Carrier.id == slot.carrier_id).first()
            if carrier:
                cookie = db.query(Cookie).filter(Cookie.carrier_id == carrier.id).first()
                if cookie:
                    cookie_flavor = cookie.flavor.value
                    cookie_status = cookie.status.value
        result.append(InventorySlotResponse(
            slot_name=slot.slot_name, x_pos=slot.x_pos, y_pos=slot.y_pos,
            carrier_id=slot.carrier_id, cookie_flavor=cookie_flavor, cookie_status=cookie_status,
        ))
    return result

# Order Endpoints
@app.post("/order/store", response_model=CommandResponse, tags=["Orders"])
def store_cookie(data: StoreRequest, db: Session = Depends(get_db)):
    if data.slot_name:
        slot = db.query(InventorySlot).filter(
            InventorySlot.slot_name == data.slot_name,
            InventorySlot.carrier_id == None
        ).first()
        if not slot:
            raise HTTPException(status_code=400, detail=f"Slot {data.slot_name} not available")
    else:
        slot = db.query(InventorySlot).filter(InventorySlot.carrier_id == None).first()
        if not slot:
            raise HTTPException(status_code=400, detail="No available slots")
    
    try:
        flavor = CookieFlavor[data.flavor.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid flavor: {data.flavor}")
    
    carrier = Carrier(current_zone="STORAGE", is_locked=False)
    db.add(carrier)
    db.flush()
    
    batch_uuid = str(uuid.uuid4())
    cookie = Cookie(batch_uuid=batch_uuid, carrier_id=carrier.id, flavor=flavor, status=CookieStatus.STORED)
    db.add(cookie)
    slot.carrier_id = carrier.id
    
    command = Command(
        command_type="STORE", target_slot=slot.slot_name,
        payload_json=json.dumps({"flavor": flavor.value, "batch_uuid": batch_uuid}),
        status="COMPLETED", executed_at=datetime.utcnow(), completed_at=datetime.utcnow(),
    )
    db.add(command)
    
    log = SystemLog(level=LogLevel.INFO, source="API", message=f"Stored {flavor.value} in {slot.slot_name}")
    db.add(log)
    db.commit()
    
    return CommandResponse(success=True, message=f"Cookie stored in {slot.slot_name}",
                          command_id=command.id, slot_name=slot.slot_name, batch_uuid=batch_uuid)

@app.post("/order/retrieve", response_model=CommandResponse, tags=["Orders"])
def retrieve_cookie(data: RetrieveRequest, db: Session = Depends(get_db)):
    slot = db.query(InventorySlot).filter(InventorySlot.slot_name == data.slot_name).first()
    if not slot:
        raise HTTPException(status_code=404, detail=f"Slot {data.slot_name} not found")
    if not slot.carrier_id:
        raise HTTPException(status_code=400, detail=f"Slot {data.slot_name} is empty")
    
    carrier = db.query(Carrier).filter(Carrier.id == slot.carrier_id).first()
    cookie = db.query(Cookie).filter(Cookie.carrier_id == carrier.id).first() if carrier else None
    batch_uuid = cookie.batch_uuid if cookie else None
    
    if cookie:
        cookie.status = CookieStatus.SHIPPED
    slot.carrier_id = None
    
    command = Command(
        command_type="RETRIEVE", target_slot=data.slot_name,
        payload_json=json.dumps({"batch_uuid": batch_uuid}),
        status="COMPLETED", executed_at=datetime.utcnow(), completed_at=datetime.utcnow(),
    )
    db.add(command)
    
    log = SystemLog(level=LogLevel.INFO, source="API", message=f"Retrieved from {data.slot_name}")
    db.add(log)
    db.commit()
    
    return CommandResponse(success=True, message=f"Retrieved from {data.slot_name}",
                          command_id=command.id, slot_name=data.slot_name, batch_uuid=batch_uuid)

# Dashboard Endpoint
@app.get("/dashboard/data", response_model=DashboardDataResponse, tags=["Dashboard"])
def get_dashboard_data(db: Session = Depends(get_db)):
    # Inventory
    slots = db.query(InventorySlot).all()
    inventory = []
    occupied_count = 0
    for slot in slots:
        cookie_flavor, cookie_status = None, None
        if slot.carrier_id:
            occupied_count += 1
            carrier = db.query(Carrier).filter(Carrier.id == slot.carrier_id).first()
            if carrier:
                cookie = db.query(Cookie).filter(Cookie.carrier_id == carrier.id).first()
                if cookie:
                    cookie_flavor = cookie.flavor.value
                    cookie_status = cookie.status.value
        inventory.append(InventorySlotResponse(
            slot_name=slot.slot_name, x_pos=slot.x_pos, y_pos=slot.y_pos,
            carrier_id=slot.carrier_id, cookie_flavor=cookie_flavor, cookie_status=cookie_status,
        ))
    
    # Hardware
    devices = db.query(HardwareState).all()
    hardware = [
        HardwareStateResponse(
            device_id=hw.device_id, current_x=hw.current_x, current_y=hw.current_y,
            current_z=hw.current_z, status=hw.status.value, updated_at=hw.updated_at,
        ) for hw in devices
    ]
    
    # Logs
    recent_logs = db.query(SystemLog).order_by(desc(SystemLog.timestamp)).limit(10).all()
    logs = [
        SystemLogResponse(id=log.id, timestamp=log.timestamp, level=log.level.value,
                         source=log.source, message=log.message)
        for log in recent_logs
    ]
    
    # Energy
    since = datetime.utcnow() - timedelta(hours=24)
    total_energy = db.query(func.sum(EnergyLog.joules)).filter(EnergyLog.timestamp >= since).scalar() or 0.0
    device_energy = db.query(EnergyLog.device_id, func.sum(EnergyLog.joules).label("total")).filter(
        EnergyLog.timestamp >= since).group_by(EnergyLog.device_id).all()
    energy = EnergyStatsResponse(
        total_joules=total_energy, total_kwh=total_energy / 3600000,
        devices={d.device_id: d.total for d in device_energy},
    )
    
    # Stats
    cookie_counts = db.query(Cookie.status, func.count(Cookie.batch_uuid)).group_by(Cookie.status).all()
    cookie_stats = {status.value: count for status, count in cookie_counts}
    active_alerts = db.query(func.count(Alert.id)).filter(Alert.acknowledged == False).scalar() or 0
    
    stats = {
        "total_slots": len(slots),
        "occupied_slots": occupied_count,
        "available_slots": len(slots) - occupied_count,
        "total_cookies": sum(cookie_stats.values()),
        "stored_cookies": cookie_stats.get("STORED", 0),
        "active_devices": len([h for h in hardware if h.status != "ERROR"]),
        "active_alerts": active_alerts,
        "system_healthy": active_alerts == 0 and all(h.status != "ERROR" for h in hardware),
    }
    
    return DashboardDataResponse(inventory=inventory, hardware=hardware, logs=logs, energy=energy, stats=stats)

# Maintenance Endpoints
@app.post("/maintenance/initialize", tags=["Maintenance"])
def initialize_system(db: Session = Depends(get_db)):
    seed_inventory_slots(db)
    seed_hardware_devices(db)
    log = SystemLog(level=LogLevel.INFO, source="MAINTENANCE", message="System initialized")
    db.add(log)
    db.commit()
    return {"success": True, "message": "System initialized"}

@app.post("/maintenance/reset", tags=["Maintenance"])
def reset_system(db: Session = Depends(get_db)):
    devices = db.query(HardwareState).all()
    for hw in devices:
        hw.current_x = 0
        hw.current_y = 0
        hw.current_z = 0
        hw.status = HardwareStatus.IDLE
    log = SystemLog(level=LogLevel.INFO, source="MAINTENANCE", message="System reset")
    db.add(log)
    db.commit()
    return {"success": True, "message": "System reset complete"}

@app.post("/maintenance/emergency-stop", tags=["Maintenance"])
def emergency_stop(db: Session = Depends(get_db)):
    devices = db.query(HardwareState).all()
    for hw in devices:
        hw.status = HardwareStatus.ERROR
        hw.last_error = "Emergency stop"
    alert = Alert(
        alert_type="EMERGENCY", severity=AlertSeverity.CRITICAL,
        title="Emergency Stop", message="All hardware stopped",
    )
    db.add(alert)
    log = SystemLog(level=LogLevel.CRITICAL, source="SAFETY", message="EMERGENCY STOP")
    db.add(log)
    db.commit()
    return {"success": True, "message": "Emergency stop activated"}

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
