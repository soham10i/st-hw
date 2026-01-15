# STF Digital Twin - Python Implementation

A warehouse automation digital twin system featuring real-time hardware simulation, MQTT communication, and a Glassmorphism dashboard.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     STF Digital Twin                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │  Streamlit   │    │   FastAPI    │    │    MySQL     │     │
│  │  Dashboard   │◄──►│   REST API   │◄──►│   Database   │     │
│  │  (Port 8501) │    │  (Port 8000) │    │  (Port 3306) │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│         │                   │                                  │
│         │                   │                                  │
│         ▼                   ▼                                  │
│  ┌──────────────────────────────────────────────────────┐     │
│  │                  MQTT Broker (Port 1883)              │     │
│  └──────────────────────────────────────────────────────┘     │
│         │                   │                   │              │
│         ▼                   ▼                   ▼              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   Mock HBW   │    │   Mock VGR   │    │  Mock Conv.  │     │
│  │  (10Hz sim)  │    │  (10Hz sim)  │    │  (10Hz sim)  │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              Main Controller (FSM Logic)              │     │
│  │  • Command translation  • Safety interlocks           │     │
│  │  • Collision prevention • Energy logging              │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Start Infrastructure (Docker)

```bash
cd stf_warehouse
docker-compose up -d
```

This starts:
- MySQL on port 3306
- Mosquitto MQTT on port 1883
- Adminer (DB UI) on port 8080

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables

```bash
export DATABASE_URL="mysql+pymysql://stf_user:stf_password@localhost:3306/stf_warehouse"
export STF_API_URL="http://localhost:8000"
export MQTT_BROKER="localhost"
export MQTT_PORT="1883"
```

### 4. Start Services (Multi-Terminal)

**Terminal 1 - FastAPI Server:**
```bash
cd stf_warehouse
python -m api.main
```

**Terminal 2 - Mock Hardware:**
```bash
cd stf_warehouse
python -m hardware.mock_hbw
```

**Terminal 3 - Main Controller:**
```bash
cd stf_warehouse
python -m controller.main_controller
```

**Terminal 4 - Streamlit Dashboard:**
```bash
cd stf_warehouse
streamlit run dashboard/app.py
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/dashboard/data` | GET | All dashboard data |
| `/inventory` | GET | List inventory slots |
| `/hardware/states` | GET | All hardware states |
| `/hardware/state` | POST | Update hardware state |
| `/order/store` | POST | Store a cookie |
| `/order/retrieve` | POST | Retrieve a cookie |
| `/telemetry` | POST | Record telemetry |
| `/energy` | POST | Record energy usage |
| `/maintenance/reset` | POST | Reset system |
| `/maintenance/emergency-stop` | POST | Emergency stop |

## MQTT Topics

### Commands (Subscribe)
- `stf/hbw/cmd/move` - Move HBW to position
- `stf/hbw/cmd/gripper` - Control gripper
- `stf/vgr/cmd/move` - Move VGR
- `stf/conveyor/cmd/start` - Start conveyor
- `stf/global/req/reset` - Reset all hardware

### Status (Publish)
- `stf/hbw/status` - HBW position/status
- `stf/vgr/status` - VGR position/status
- `stf/conveyor/status` - Conveyor status

## Database Schema

| Table | Description |
|-------|-------------|
| `py_carriers` | Carrier entities |
| `py_cookies` | Cookie batches |
| `py_inventory_slots` | 3x3 rack grid |
| `py_hardware_states` | Device positions |
| `py_system_logs` | System logs |
| `py_energy_logs` | Energy consumption |
| `py_telemetry_history` | Time-series data |
| `py_alerts` | System alerts |
| `py_commands` | Command history |

## Coordinate System

| Slot | X | Y |
|------|---|---|
| A1 | 100 | 100 |
| A2 | 200 | 100 |
| A3 | 300 | 100 |
| B1 | 100 | 200 |
| B2 | 200 | 200 |
| B3 | 300 | 200 |
| C1 | 100 | 300 |
| C2 | 200 | 300 |
| C3 | 300 | 300 |

## Dashboard Features

- **Industrial Apple Glassmorphism** design
- **Live 2D robot position** monitoring
- **3x3 inventory grid** with color-coded cookies
- **Control panel** for store/retrieve operations
- **Hardware status** indicators
- **System logs** display
- **Energy consumption** metrics
- **Auto-refresh** every 2 seconds

## Safety Features

- **Collision Prevention**: Blocks movements that would cause hardware collision
- **Emergency Stop**: Immediately halts all hardware
- **Alert System**: Logs critical events and sends notifications
- **FSM Logic**: Ensures proper state transitions
