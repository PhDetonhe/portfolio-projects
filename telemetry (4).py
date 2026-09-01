from fastapi import APIRouter

from app.schemas.telemetry import TelemetryCreate, TelemetryResponse
from app.services import telemetry_service

router = APIRouter(prefix="/devices", tags=["Telemetry"])


@router.post("/{device_id}/telemetry", response_model=TelemetryResponse, status_code=201)
def create_telemetry(device_id: str, data: TelemetryCreate):
    doc = telemetry_service.create_telemetry(device_id, data)
    return {**doc, "id": doc["_id"]}
