from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import FastAPI, HTTPException
from  pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


client = MongoClient(
    "mongodb://localhost:27017/"
)

db = client["aquamonitor"]

stations_collection = db["stations"]


# ============================
# POST
# ============================

@app.post("/api/stations")
def create_station(station: dict):

    print("Database:", db.name)
    print("Collection:", stations_collection.name)
    print("Document:", station)

    result = stations_collection.insert_one(station)

    print("Inserted ID:", result.inserted_id)

    return {
        "message": "Station created successfully",
        "id": str(result.inserted_id)
    }

# ============================
# GET
# ============================
@app.get("/api/stations")
def get_stations():

    stations = stations_collection.find()

    result = []

    for station in stations:
        result.append({
            "station_id": station["station_id"],
            "location": station["location"],
            "detections": station["detections"]
        })

    return result

# ============================
# DELETE: permitir deletar a estação por enquanto
# ============================
@app.delete("/api/stations/{station_id}")
def delete_station(station_id: str):

    try:
        station_id = int(station_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Station ID must be a number"
        )

    result = stations_collection.delete_one({
        "station_id": station_id
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Station not found"
        )

    return {
        "message": "Station deleted successfully"
    }


# ============================
# Update(não existem motivos por enquanto))
# ============================

# ============================
# Receber dados de detecção de uma estação(endpoint que Raspberry Pi vai usar)
# ============================
detection_events_collection = db["detection_events"]


class DetectionEvent(BaseModel):
    """Contrato recebido da Raspberry Pi para cada resíduo contado."""

    event_id: UUID
    station_id: int = Field(gt=0)
    detection_type: Literal["bottle", "can", "carton", "paper", "plastic"]
    confidence: float = Field(ge=0, le=1)
    track_id: int = Field(gt=0)
    detected_at: datetime


@app.post("/api/detections")
def create_detection_event(event: DetectionEvent):
    # JSON seguro para MongoDB: UUID e data seguem como strings ISO-8601.
    event_document = event.model_dump(mode="json") if hasattr(event, "model_dump") else event.dict()
    event_document["event_id"] = str(event_document["event_id"])
    event_document["detected_at"] = event.detected_at.isoformat()
    station_id = event.station_id

    station = stations_collection.find_one({"station_id": station_id})

    if not station:
        raise HTTPException(
            status_code=404,
            detail="Station not found"
        )

    # A estação pode reenviar a mesma requisição após uma falha de rede. Não
    # incrementamos ``detections`` duas vezes para o mesmo evento.
    if detection_events_collection.find_one({"event_id": event_document["event_id"]}):
        return {"message": "Detection already saved", "station_id": station_id}

    detection_events_collection.insert_one(event_document)

    stations_collection.update_one(
        {"station_id": station_id},
        {"$inc": {"detections": 1}}
    )

    return {
        "message": "Detection saved successfully",
        "station_id": station_id
    }
