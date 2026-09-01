from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.database.connection import cncs_collection, devices_collection, telemetry_collection
from app.services.device_service import is_online


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _next_code() -> str:
    """
    Gera CNC01, CNC02, ... de forma simples: tenta o próximo número a partir
    da contagem atual de documentos e avança até achar um código livre.
    Suficiente para o volume de cadastros manuais esperado nesta V1;
    colisões concorrentes são tratadas com retry (unique index + DuplicateKeyError).
    """
    candidate = cncs_collection.count_documents({}) + 1
    for _ in range(1000):
        code = f"CNC{candidate:02d}"
        if not cncs_collection.find_one({"code": code}):
            return code
        candidate += 1
    raise HTTPException(status_code=500, detail="Não foi possível gerar código para a CNC")


def create_cnc(name: str, description: Optional[str]) -> dict:
    for _ in range(5):
        doc = {
            "_id": str(uuid4()),
            "code": _next_code(),
            "name": name,
            "description": description,
            "status": "UNKNOWN",
            "status_since": None,
            "last_seen": None,
            "created_at": utcnow(),
        }
        try:
            cncs_collection.insert_one(doc)
            return doc
        except DuplicateKeyError:
            continue
    raise HTTPException(status_code=500, detail="Não foi possível criar a CNC (colisão de código)")


def get_cnc_or_404(cnc_id: str) -> dict:
    doc = cncs_collection.find_one({"_id": cnc_id})
    if not doc:
        raise HTTPException(status_code=404, detail="CNC não encontrada")
    return doc


def list_cncs() -> list[dict]:
    return list(cncs_collection.find().sort("code", 1))


def update_cnc(cnc_id: str, changes: dict) -> dict:
    get_cnc_or_404(cnc_id)
    if changes:
        cncs_collection.update_one({"_id": cnc_id}, {"$set": changes})
    return get_cnc_or_404(cnc_id)


def delete_cnc(cnc_id: str) -> None:
    """
    O MongoDB não possui cascade. Decisão da V1: ao excluir uma CNC,
    excluímos também os Devices associados e as Telemetrias desses Devices,
    para não deixar referências quebradas (device.cnc_id / telemetry.device_id
    apontando para registros inexistentes).
    """
    get_cnc_or_404(cnc_id)
    device_ids = [d["_id"] for d in devices_collection.find({"cnc_id": cnc_id}, {"_id": 1})]
    if device_ids:
        telemetry_collection.delete_many({"device_id": {"$in": device_ids}})
        devices_collection.delete_many({"cnc_id": cnc_id})
    cncs_collection.delete_one({"_id": cnc_id})


def set_status(cnc_id: str, status: str, when: datetime) -> None:
    """Chamado quando chega telemetria: atualiza status/last_seen da CNC."""
    cnc = get_cnc_or_404(cnc_id)
    update = {"last_seen": when}
    if cnc["status"] != status:
        update["status"] = status
        update["status_since"] = when
    cncs_collection.update_one({"_id": cnc_id}, {"$set": update})


def get_status(cnc_id: str) -> dict:
    """
    Monta a resposta de status calculando a duração dinamicamente
    (status_since -> agora), sem armazenar contadores.

    Decisão: como não há agendador de tarefas nesta V1, a transição para
    UNKNOWN por gateway offline é feita de forma "preguiçosa" (lazy): sempre
    que o status é consultado, se o gateway estiver offline e o status
    persistido ainda não for UNKNOWN, o backend registra a transição
    (status = UNKNOWN, status_since = agora) antes de responder. Isso evita
    a necessidade de um processo em background rodando a cada poucos
    segundos apenas para expirar dispositivos.
    """
    cnc = get_cnc_or_404(cnc_id)
    device = devices_collection.find_one({"cnc_id": cnc_id})
    now = utcnow()

    gateway_online = is_online(device.get("last_seen")) if device else False

    if not gateway_online and cnc["status"] != "UNKNOWN":
        cncs_collection.update_one(
            {"_id": cnc_id}, {"$set": {"status": "UNKNOWN", "status_since": now}}
        )
        cnc = get_cnc_or_404(cnc_id)

    reading = None
    if device:
        reading = telemetry_collection.find_one({"device_id": device["_id"]}, sort=[("timestamp", -1)])

    duration = int((now - cnc["status_since"]).total_seconds()) if cnc.get("status_since") else 0

    return {
        "id": cnc["_id"],
        "code": cnc["code"],
        "name": cnc["name"],
        "status": cnc["status"],
        "status_since": cnc.get("status_since"),
        "status_duration_seconds": max(0, duration),
        "last_seen": cnc.get("last_seen"),
        "gateway_online": gateway_online,
        "device_code": device["code"] if device else None,
        "digital_signals": reading.get("digital_signals") if reading else {},
        "analog_signals": reading.get("analog_signals") if reading else {},
        "voltage_24v": reading.get("voltage_24v") if reading else None,
    }
