def test_register_new_device_generates_code_dvc01(client):
    resp = client.post(
        "/devices/register",
        json={"mac_address": "a4:cf:12:8b:34:91", "ip_address": "192.168.1.37"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "DVC01"
    assert body["mac_address"] == "A4:CF:12:8B:34:91"
    assert body["cnc_id"] is None


def test_register_second_device_generates_code_dvc02(client):
    client.post("/devices/register", json={"mac_address": "AA:BB:CC:DD:EE:01"})
    resp = client.post("/devices/register", json={"mac_address": "AA:BB:CC:DD:EE:02"})
    assert resp.json()["code"] == "DVC02"


def test_register_existing_mac_does_not_duplicate_device(client):
    first = client.post("/devices/register", json={"mac_address": "AA:BB:CC:DD:EE:03"}).json()
    second = client.post(
        "/devices/register",
        json={"mac_address": "AA:BB:CC:DD:EE:03", "ip_address": "10.0.0.5"},
    ).json()
    assert first["id"] == second["id"]
    assert second["ip_address"] == "10.0.0.5"
    assert client.get("/devices").json().__len__() == 1


def test_register_invalid_mac_returns_422(client):
    resp = client.post("/devices/register", json={"mac_address": "not-a-mac"})
    assert resp.status_code == 422


def test_associate_device_to_cnc(client):
    cnc = client.post("/cncs", json={"name": "CNC"}).json()
    device = client.post("/devices/register", json={"mac_address": "AA:BB:CC:DD:EE:04"}).json()

    resp = client.put(f"/devices/{device['id']}", json={"cnc_id": cnc["id"]})
    assert resp.status_code == 200
    assert resp.json()["cnc_id"] == cnc["id"]


def test_associate_device_to_nonexistent_cnc_returns_422(client):
    device = client.post("/devices/register", json={"mac_address": "AA:BB:CC:DD:EE:05"}).json()
    resp = client.put(f"/devices/{device['id']}", json={"cnc_id": "does-not-exist"})
    assert resp.status_code == 422


def test_get_nonexistent_device_returns_404(client):
    assert client.get("/devices/does-not-exist").status_code == 404


def test_delete_device(client):
    device = client.post("/devices/register", json={"mac_address": "AA:BB:CC:DD:EE:06"}).json()
    resp = client.delete(f"/devices/{device['id']}")
    assert resp.status_code == 204
    assert client.get(f"/devices/{device['id']}").status_code == 404


def test_device_status_online_right_after_register(client):
    device = client.post("/devices/register", json={"mac_address": "AA:BB:CC:DD:EE:07"}).json()
    status = client.get(f"/devices/{device['id']}/status").json()
    assert status["online"] is True
