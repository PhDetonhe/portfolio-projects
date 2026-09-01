from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from app.schemas.cnc import CNCCreate, CNCResponse, CNCStatusResponse, CNCUpdate
from app.schemas.telemetry import TelemetryHistoryResponse
from app.services import cnc_service, telemetry_service

router = APIRouter(prefix="/cncs", tags=["CNC"])


def _to_response(doc: dict) -> dict:
    return {**doc, "id": doc["_id"]}


@router.post("", response_model=CNCResponse, status_code=201)
def create_cnc(data: CNCCreate):
    doc = cnc_service.create_cnc(data.name, data.description)
    return _to_response(doc)


@router.get("", response_model=list[CNCResponse])
def list_cncs():
    return [_to_response(doc) for doc in cnc_service.list_cncs()]


@router.get("/{cnc_id}", response_model=CNCResponse)
def get_cnc(cnc_id: str):
    return _to_response(cnc_service.get_cnc_or_404(cnc_id))


@router.put("/{cnc_id}", response_model=CNCResponse)
def update_cnc(cnc_id: str, data: CNCUpdate):
    changes = data.model_dump(exclude_unset=True)
    doc = cnc_service.update_cnc(cnc_id, changes)
    return _to_response(doc)


@router.delete("/{cnc_id}", status_code=204)
def delete_cnc(cnc_id: str):
    cnc_service.delete_cnc(cnc_id)


@router.get("/{cnc_id}/status", response_model=CNCStatusResponse)
def get_cnc_status(cnc_id: str):
    return cnc_service.get_status(cnc_id)


@router.get("/{cnc_id}/history", response_model=TelemetryHistoryResponse)
def get_cnc_history(
    cnc_id: str,
    start: Optional[datetime] = Query(default=None),
    end: Optional[datetime] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=500),
):
    cnc_service.get_cnc_or_404(cnc_id)
    items, total = telemetry_service.get_history(cnc_id=cnc_id, start=start, end=end, page=page, limit=limit)
    return TelemetryHistoryResponse(
        items=[{**item, "id": item["_id"]} for item in items],
        total=total,
        page=page,
        limit=limit,
    )
