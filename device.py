import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

MAC_ADDRESS_RE = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")


class DeviceRegister(BaseModel):
    """Payload enviado pela ESP32 no primeiro contato (e nos seguintes)."""

    mac_address: str
    ip_address: Optional[str] = Field(default=None, max_length=45)
    firmware_version: Optional[str] = Field(default=None, max_length=50)
    name: Optional[str] = Field(default=None, max_length=255)

    @field_validator("mac_address")
    @classmethod
    def validate_mac_address(cls, value: str) -> str:
        value = value.strip().upper()
        if not MAC_ADDRESS_RE.match(value):
            raise ValueError("mac_address inválido, formato esperado AA:BB:CC:DD:EE:FF")
        return value


class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    firmware_version: Optional[str] = Field(default=None, max_length=50)
    # Um gateway físico pode ser realocado para outra CNC (troca de armário,
    # substituição de máquina, reorganização de planta), por isso é permitido.
    cnc_id: Optional[str] = None


class DeviceResponse(BaseModel):
    id: str
    code: str
    name: str
    mac_address: str
    ip_address: Optional[str] = None
    cnc_id: Optional[str] = None
    firmware_version: Optional[str] = None
    last_seen: Optional[datetime] = None
    online: bool
    created_at: datetime


class DeviceStatusResponse(BaseModel):
    id: str
    code: str
    name: str
    cnc_id: Optional[str] = None
    online: bool
    last_seen: Optional[datetime] = None
