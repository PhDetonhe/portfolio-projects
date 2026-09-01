def test_create_cnc_generates_code_cnc01(client):
    resp = client.post("/cncs", json={"name": "Centro de Usinagem 01"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "CNC01"
    assert body["status"] == "UNKNOWN"


def test_create_second_cnc_generates_code_cnc02(client):
    client.post("/cncs", json={"name": "CNC 1"})
    resp = client.post("/cncs", json={"name": "CNC 2"})
    assert resp.json()["code"] == "CNC02"


def test_get_nonexistent_cnc_returns_404(client):
    resp = client.get("/cncs/does-not-exist")
    assert resp.status_code == 404


def test_update_cnc(client):
    cnc = client.post("/cncs", json={"name": "Original"}).json()
    resp = client.put(f"/cncs/{cnc['id']}", json={"name": "Atualizada"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Atualizada"


def test_delete_cnc_removes_devices_and_telemetry(client):
    cnc = client.post("/cncs", json={"name": "CNC"}).json()
    device = client.post(
        "/devices/register", json={"mac_address": "AA:BB:CC:DD:EE:01"}
    ).json()
    client.put(f"/devices/{device['id']}", json={"cnc_id": cnc["id"]})
    client.post(
        f"/devices/{device['id']}/telemetry",
        json={"machine_active": True, "voltage_24v": True},
    )

    resp = client.delete(f"/cncs/{cnc['id']}")
    assert resp.status_code == 204
    assert client.get(f"/cncs/{cnc['id']}").status_code == 404
    assert client.get(f"/devices/{device['id']}").status_code == 404


def test_status_duration_is_calculated(client):
    cnc = client.post("/cncs", json={"name": "CNC"}).json()
    device = client.post(
        "/devices/register", json={"mac_address": "AA:BB:CC:DD:EE:02"}
    ).json()
    client.put(f"/devices/{device['id']}", json={"cnc_id": cnc["id"]})
    client.post(
        f"/devices/{device['id']}/telemetry",
        json={"machine_active": True, "voltage_24v": True},
    )

    status = client.get(f"/cncs/{cnc['id']}/status").json()
    assert status["status"] == "ACTIVE"
    assert status["status_duration_seconds"] >= 0
    assert status["gateway_online"] is True


def test_status_active_to_inactive_updates_status_since(client):
    cnc = client.post("/cncs", json={"name": "CNC"}).json()
    device = client.post(
        "/devices/register", json={"mac_address": "AA:BB:CC:DD:EE:03"}
    ).json()
    client.put(f"/devices/{device['id']}", json={"cnc_id": cnc["id"]})

    client.post(f"/devices/{device['id']}/telemetry", json={"machine_active": True, "voltage_24v": True})
    first_status = client.get(f"/cncs/{cnc['id']}/status").json()
    assert first_status["status"] == "ACTIVE"
    first_since = first_status["status_since"]

    client.post(f"/devices/{device['id']}/telemetry", json={"machine_active": False, "voltage_24v": True})
    second_status = client.get(f"/cncs/{cnc['id']}/status").json()
    assert second_status["status"] == "INACTIVE"
    assert second_status["status_since"] != first_since
