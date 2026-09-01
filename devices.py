from fastapi import APIRouter

from app.schemas.device import DeviceRegister, DeviceResponse, DeviceStatusResponse, DeviceUpdate
from app.services import device_service

router = APIRouter(prefix="/devices", tags=["Devices"])


def _to_response(doc: dict) -> dict:
    return {**doc, "id": doc["_id"], "online": device_service.is_online(doc.get("last_seen"))}


@router.post("/register", response_model=DeviceResponse, status_code=201)
def register_device(data: DeviceRegister):
    doc = device_service.register_device(data.mac_address, data.ip_address, data.firmware_version, data.name)
    return _to_response(doc)


@router.get("", response_model=list[DeviceResponse])
def list_devices():
    return [_to_response(doc) for doc in device_service.list_devices()]


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: str):
    return _to_response(device_service.get_device_or_404(device_id))


@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(device_id: str, data: DeviceUpdate):
    changes = data.model_dump(exclude_unset=True)
    doc = device_service.update_device(device_id, changes)
    return _to_response(doc)


@router.delete("/{device_id}", status_code=204)
def delete_device(device_id: str):
    device_service.delete_device(device_id)


@router.get("/{device_id}/status", response_model=DeviceStatusResponse)
def get_device_status(device_id: str):
    doc = device_service.get_device_or_404(device_id)
    return {
        "id": doc["_id"],
        "code": doc["code"],
        "name": doc["name"],
        "cnc_id": doc.get("cnc_id"),
        "online": device_service.is_online(doc.get("last_seen")),
        "last_seen": doc.get("last_seen"),
    }
