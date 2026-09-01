from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.database.connection import cncs_collection, devices_collection, telemetry_collection

# Regra única para online/offline, usada em todo o projeto (não espalhar o "5").
DEVICE_ONLINE_TIMEOUT_SECONDS = 5


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def is_online(last_seen: Optional[datetime]) -> bool:
    """
    Decisão: 'online' não é armazenado no banco. É sempre calculado a partir
    de last_seen no momento da leitura, para nunca ficar dessincronizado
    (ex.: campo 'online=true' salvo, mas o dispositivo já parou de enviar
    dados há minutos).
    """
    if not last_seen:
        return False
    return (utcnow() - last_seen).total_seconds() <= DEVICE_ONLINE_TIMEOUT_SECONDS


def _next_code() -> str:
    candidate = devices_collection.count_documents({}) + 1
    for _ in range(1000):
        code = f"DVC{candidate:02d}"
        if not devices_collection.find_one({"code": code}):
            return code
        candidate += 1
    raise HTTPException(status_code=500, detail="Não foi possível gerar código para o dispositivo")


def register_device(
    mac_address: str,
    ip_address: Optional[str],
    firmware_version: Optional[str],
    name: Optional[str],
) -> dict:
    """
    Primeiro contato (ou contatos seguintes) da ESP32 com o backend.
    Se o MAC já existir, apenas reconhece e atualiza o Device.
    Se não existir, cria automaticamente (sem CNC associada).
    """
    now = utcnow()
    existing = devices_collection.find_one({"mac_address": mac_address})
    if existing:
        update = {"last_seen": now}
        if ip_address:
            update["ip_address"] = ip_address
        if firmware_version:
            update["firmware_version"] = firmware_version
        devices_collection.update_one({"_id": existing["_id"]}, {"$set": update})
        return devices_collection.find_one({"_id": existing["_id"]})

    for _ in range(5):
        doc = {
            "_id": str(uuid4()),
            "code": _next_code(),
            "name": name or f"Gateway {mac_address}",
            "mac_address": mac_address,
            "ip_address": ip_address,
            "cnc_id": None,
            "firmware_version": firmware_version,
            "last_seen": now,
            "created_at": now,
        }
        try:
            devices_collection.insert_one(doc)
            return doc
        except DuplicateKeyError:
            # colisão de code ou (raro) de mac_address inserido em paralelo
            if devices_collection.find_one({"mac_address": mac_address}):
                return devices_collection.find_one({"mac_address": mac_address})
            continue
    raise HTTPException(status_code=500, detail="Não foi possível registrar o dispositivo (colisão)")


def get_device_or_404(device_id: str) -> dict:
    doc = devices_collection.find_one({"_id": device_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    return doc


def list_devices() -> list[dict]:
    return list(devices_collection.find().sort("code", 1))


def update_device(device_id: str, changes: dict) -> dict:
    get_device_or_404(device_id)
    if "cnc_id" in changes and changes["cnc_id"] is not None:
        if not cncs_collection.find_one({"_id": changes["cnc_id"]}):
            raise HTTPException(status_code=422, detail="CNC associada não encontrada")
    if changes:
        devices_collection.update_one({"_id": device_id}, {"$set": changes})
    return get_device_or_404(device_id)


def delete_device(device_id: str) -> None:
    get_device_or_404(device_id)
    telemetry_collection.delete_many({"device_id": device_id})
    devices_collection.delete_one({"_id": device_id})


def touch_last_seen(device_id: str, when: datetime) -> None:
    devices_collection.update_one({"_id": device_id}, {"$set": {"last_seen": when}})
