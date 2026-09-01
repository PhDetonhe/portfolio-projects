from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.connection import check_connection, create_indexes
from app.routers import cnc, devices, telemetry


@asynccontextmanager
async def lifespan(app: FastAPI):
    check_connection()
    create_indexes()
    yield


app = FastAPI(
    title="SCOMPTEC - CNC Monitor",
    description="Backend V1 para monitoramento de máquinas CNC industriais via gateways ESP32.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cnc.router)
app.include_router(devices.router)
app.include_router(telemetry.router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
