import os

# Precisa ser definido ANTES de qualquer import de app.* para que
# app/database/connection.py use mongomock em vez do MongoDB real.
os.environ["MONGO_TEST"] = "1"

import pytest
from fastapi.testclient import TestClient

from app.database.connection import cncs_collection, devices_collection, telemetry_collection, create_indexes
from app.main import app


@pytest.fixture(autouse=True)
def clean_db():
    cncs_collection.delete_many({})
    devices_collection.delete_many({})
    telemetry_collection.delete_many({})
    create_indexes()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
