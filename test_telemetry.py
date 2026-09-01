from datetime import datetime, timedelta, timezone

from app.database.connection import devices_collection


def _register_device_with_cnc(client, mac):
    cnc = client.post("/cncs", json={"name": "CNC Teste"}).json()
    device = client.post("/devices/register", json={"mac_address": mac}).json()
    client.put(f"/devices/{device['id']}", json={"cnc_id": cnc["id"]})
    return cnc, device


def test_send_telemetry_updates_last_seen_and_cnc_status(client):
    cnc, device = _register_device_with_cnc(client, "AA:BB:CC:DD:EE:10")

    resp = client.post(
        f"/devices/{device['id']}/telemetry",
        json={
            "machine_active": True,
            "voltage_24v": True,
            "digital_signals": {"D01": True},
            "analog_signals": {"A01": 3.42},
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["device_id"] == device["id"]
    assert "received_at" in body

    device_status = client.get(f"/devices/{device['id']}/status").json()
    assert device_status["online"] is True
    assert device_status["last_seen"] is not None

    cnc_status = client.get(f"/cncs/{cnc['id']}/status").json()
    assert cnc_status["status"] == "ACTIVE"
    assert cnc_status["digital_signals"] == {"D01": True}


def test_telemetry_for_unknown_device_returns_404(client):
    resp = client.post(
        "/devices/does-not-exist/telemetry",
        json={"machine_active": True, "voltage_24v": True},
    )
    assert resp.status_code == 404


def test_gateway_offline_marks_cnc_unknown(client):
    cnc, device = _register_device_with_cnc(client, "AA:BB:CC:DD:EE:11")
    client.post(
        f"/devices/{device['id']}/telemetry",
        json={"machine_active": True, "voltage_24v": True},
    )
    assert client.get(f"/cncs/{cnc['id']}/status").json()["status"] == "ACTIVE"

    # Simula silêncio do gateway: força last_seen para o passado.
    stale = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=30)
    devices_collection.update_one({"_id": device["id"]}, {"$set": {"last_seen": stale}})

    device_status = client.get(f"/devices/{device['id']}/status").json()
    assert device_status["online"] is False

    cnc_status = client.get(f"/cncs/{cnc['id']}/status").json()
    assert cnc_status["status"] == "UNKNOWN"
    assert cnc_status["gateway_online"] is False


def test_history_pagination(client):
    cnc, device = _register_device_with_cnc(client, "AA:BB:CC:DD:EE:12")
    for _ in range(3):
        client.post(
            f"/devices/{device['id']}/telemetry",
            json={"machine_active": True, "voltage_24v": True},
        )

    resp = client.get(f"/cncs/{cnc['id']}/history?limit=2&page=1")
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
