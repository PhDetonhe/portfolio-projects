from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class CNCCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)


class CNCUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)


class CNCResponse(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str] = None
    status: str
    status_since: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    created_at: datetime


class CNCStatusResponse(BaseModel):
    id: str
    code: str
    name: str
    status: str
    status_since: Optional[datetime] = None
    status_duration_seconds: int
    last_seen: Optional[datetime] = None
    gateway_online: bool
    device_code: Optional[str] = None
    digital_signals: Optional[Dict[str, Any]] = None
    analog_signals: Optional[Dict[str, Any]] = None
    voltage_24v: Optional[bool] = None
