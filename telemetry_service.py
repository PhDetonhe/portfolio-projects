from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from app.database.connection import devices_collection, telemetry_collection
from app.schemas.telemetry import TelemetryCreate
from app.services import cnc_service, device_service


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalize_datetime(value: Optional[datetime]) -> datetime:
    if value is None:
        return utcnow()
    if value.tzinfo:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def create_telemetry(device_id: str, data: TelemetryCreate) -> dict:
    device = device_service.get_device_or_404(device_id)
    occurred_at = normalize_datetime(data.timestamp)

    doc = {
        "_id": str(uuid4()),
        "device_id": device_id,
        "timestamp": occurred_at,
        "received_at": utcnow(),
        "machine_active": data.machine_active,
        "voltage_24v": data.voltage_24v,
        "digital_signals": data.digital_signals or {},
        "analog_signals": data.analog_signals or {},
        "extra_signals": data.extra_signals or {},
    }
    telemetry_collection.insert_one(doc)

    device_service.touch_last_seen(device_id, occurred_at)

    if device.get("cnc_id"):
        # Regra da V1: machine_active define ACTIVE/INACTIVE da CNC associada.
        next_status = "ACTIVE" if data.machine_active else "INACTIVE"
        cnc_service.set_status(device["cnc_id"], next_status, occurred_at)

    return doc


def get_history(
    cnc_id: Optional[str] = None,
    device_id: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    page: int = 1,
    limit: int = 50,
) -> tuple[list[dict], int]:
    query: dict = {}

    if cnc_id:
        device_ids = [d["_id"] for d in devices_collection.find({"cnc_id": cnc_id}, {"_id": 1})]
        query["device_id"] = {"$in": device_ids}
    elif device_id:
        query["device_id"] = device_id

    if start or end:
        query["timestamp"] = {}
        if start:
            query["timestamp"]["$gte"] = normalize_datetime(start)
        if end:
            query["timestamp"]["$lte"] = normalize_datetime(end)

    total = telemetry_collection.count_documents(query)
    items = list(
        telemetry_collection.find(query)
        .sort("timestamp", -1)
        .skip((page - 1) * limit)
        .limit(limit)
    )
    return items, total
