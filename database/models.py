"""
STF Digital Twin - SQLAlchemy Database Models
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Enum, Text, create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os

Base = declarative_base()

# Enums
class CookieFlavor(PyEnum):
    CHOCO = "CHOCO"
    VANILLA = "VANILLA"
    STRAWBERRY = "STRAWBERRY"

class CookieStatus(PyEnum):
    BAKING = "BAKING"
    STORED = "STORED"
    SHIPPED = "SHIPPED"

class HardwareStatus(PyEnum):
    IDLE = "IDLE"
    MOVING = "MOVING"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"

class LogLevel(PyEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class AlertSeverity(PyEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

# Models
class Carrier(Base):
    __tablename__ = "py_carriers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    current_zone = Column(String(50), nullable=False, default="STORAGE")
    is_locked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    cookies = relationship("Cookie", back_populates="carrier")
    inventory_slot = relationship("InventorySlot", back_populates="carrier", uselist=False)

class Cookie(Base):
    __tablename__ = "py_cookies"
    batch_uuid = Column(String(36), primary_key=True)
    carrier_id = Column(Integer, ForeignKey("py_carriers.id"), nullable=True)
    flavor = Column(Enum(CookieFlavor), nullable=False, default=CookieFlavor.CHOCO)
    status = Column(Enum(CookieStatus), nullable=False, default=CookieStatus.BAKING)
    expiry_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    carrier = relationship("Carrier", back_populates="cookies")

class InventorySlot(Base):
    __tablename__ = "py_inventory_slots"
    slot_name = Column(String(10), primary_key=True)
    x_pos = Column(Integer, nullable=False)
    y_pos = Column(Integer, nullable=False)
    carrier_id = Column(Integer, ForeignKey("py_carriers.id"), nullable=True, unique=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    carrier = relationship("Carrier", back_populates="inventory_slot")

class HardwareState(Base):
    __tablename__ = "py_hardware_states"
    device_id = Column(String(50), primary_key=True)
    current_x = Column(Float, nullable=False, default=0.0)
    current_y = Column(Float, nullable=False, default=0.0)
    current_z = Column(Float, nullable=False, default=0.0)
    target_x = Column(Float, nullable=True)
    target_y = Column(Float, nullable=True)
    target_z = Column(Float, nullable=True)
    status = Column(Enum(HardwareStatus), nullable=False, default=HardwareStatus.IDLE)
    last_error = Column(Text, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class SystemLog(Base):
    __tablename__ = "py_system_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    level = Column(Enum(LogLevel), nullable=False, default=LogLevel.INFO)
    source = Column(String(100), nullable=True)
    message = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)

class EnergyLog(Base):
    __tablename__ = "py_energy_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(50), nullable=False, index=True)
    joules = Column(Float, nullable=False, default=0.0)
    voltage = Column(Float, nullable=False, default=24.0)
    current_amps = Column(Float, nullable=True)
    power_watts = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

class TelemetryHistory(Base):
    __tablename__ = "py_telemetry_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(50), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

class Alert(Base):
    __tablename__ = "py_alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False, default=AlertSeverity.MEDIUM)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    device_id = Column(String(50), nullable=True)
    acknowledged = Column(Boolean, nullable=False, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

class Command(Base):
    __tablename__ = "py_commands"
    id = Column(Integer, primary_key=True, autoincrement=True)
    command_type = Column(String(50), nullable=False)
    target_slot = Column(String(10), nullable=True)
    payload_json = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

# Coordinate mapping
SLOT_COORDINATES = {
    "A1": (100, 100), "A2": (200, 100), "A3": (300, 100),
    "B1": (100, 200), "B2": (200, 200), "B3": (300, 200),
    "C1": (100, 300), "C2": (200, 300), "C3": (300, 300),
}

def get_slot_coordinates(slot_name: str) -> tuple:
    return SLOT_COORDINATES.get(slot_name, (0, 0))

def seed_inventory_slots(session):
    for slot_name, (x, y) in SLOT_COORDINATES.items():
        existing = session.query(InventorySlot).filter_by(slot_name=slot_name).first()
        if not existing:
            slot = InventorySlot(slot_name=slot_name, x_pos=x, y_pos=y)
            session.add(slot)
    session.commit()

def seed_hardware_devices(session):
    devices = [
        {"device_id": "HBW", "current_x": 0, "current_y": 0, "current_z": 0},
        {"device_id": "VGR", "current_x": 0, "current_y": 0, "current_z": 0},
        {"device_id": "CONVEYOR", "current_x": 0, "current_y": 0, "current_z": 0},
    ]
    for device in devices:
        existing = session.query(HardwareState).filter_by(device_id=device["device_id"]).first()
        if not existing:
            hw = HardwareState(**device)
            session.add(hw)
    session.commit()
