import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import Server as server
from signals import normalize
spec = importlib.util.spec_from_file_location('bridge', ROOT.parent / 'scomptec_simulador/servidor/ponte_usb.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

MESA = {'dispositivo':'opta1','uptime_ms':500,'sequencia':1,
        'estado':'acionando_queda1','machine_active':True,'voltage_24v':None,
        'digital_signals':{'ciclo':True,'alarme':False,'emergencia':None},
        'analog_signals':{'current':4.3,'voltage':24.,'power_kw':.1032},
        'extra_signals':{'simulation':True,'analog_values_simulated':True},
        'contadores':{'iniciadas':6,'reto':1,'queda1':2,'queda2':1,'falhas':1},
        'entradas':{'I2':0},'saidas':{'O1':1,'O2':1,'O3':0}}


class IntegrationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        server.app.config.update(TESTING=True, DATABASE=str(Path(self.tmp.name)/'telemetry.db'))
        server.latest, server.received, server.version = {}, None, 0
        self.client = server.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def test_usb_chunks_http_storage_and_frontend(self):
        frames = bridge.Frames()
        text = 'CNC_JSON:' + json.dumps(MESA)
        payload = None
        for start in range(0, len(text), 32):
            self.assertIsNone(frames.feed('I2 -> LOW'))
            payload = frames.feed('CNC_CHUNK:' + text[start:start+32])
        self.assertEqual(payload, MESA)
        httpd = make_server('127.0.0.1', 0, server.app)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            self.assertEqual(bridge.post(f'http://127.0.0.1:{httpd.server_port}/api/telemetria', payload), 200)
        finally:
            httpd.shutdown(); thread.join(); httpd.server_close()
        data = self.client.get('/api/status').json
        self.assertEqual(data['status'], 'OPERANDO')
        self.assertEqual(data['extra_signals']['parts_count'], 4)
        self.assertIsNone(data['digital_signals']['emergencia'])
        self.assertEqual(data['entradas'], MESA['entradas'])
        self.assertTrue(data['is_online'])
        self.assertEqual(len(self.client.get('/api/history').json['items']), 1)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        response.close()
        self.assertEqual(self.client.get('/api/telemetria').json['latest']['status'], 'OPERANDO')

    def test_status_priority_and_unknown(self):
        for power, emergency, alarm, cycle, expected in [
            (False,True,True,True,'DESLIGADA'), (True,True,True,True,'EMERGENCIA'),
            (True,False,True,True,'ALARME'), (True,False,False,True,'OPERANDO'),
            (True,False,False,False,'PARADA'), (None,None,None,None,'DESCONHECIDA')]:
            body = {'device_id':'cnc','voltage_24v':power,'digital_signals':{'emergencia':emergency,'alarme':alarm,'ciclo':cycle}}
            self.assertEqual(normalize(body)['status'], expected)

    def test_teammates_esp_payload(self):
        data = normalize({'esp_id':'ESP-1','machine_id':'MACHINE-1','digital_signal':True,'machine_state':'RUNNING','uptime_ms':10})
        self.assertEqual(data['device_id'], 'ESP-1')
        self.assertEqual(data['status'], 'OPERANDO')
        self.assertIsNone(data['voltage_24v'])
        self.assertEqual(data['analog_signals'], {})

    def test_legacy_motor_payload_and_temperature(self):
        data = normalize({'device_id':'dual','motor1_on':False,'motor2_on':True,'simulated_temperature_c':30})
        self.assertEqual(data['status'], 'OPERANDO')
        self.assertTrue(data['extra_signals']['temperature_simulated'])

    def test_rejects_invalid_frames(self):
        for body in [[], {}, {'device_id':'cnc'}, {**MESA,'digital_signals':[]},
                     {**MESA,'machine_active':'false'}, {**MESA,'analog_signals':{'current':float('nan')}}]:
            self.assertEqual(self.client.post('/api/telemetry',json=body).status_code,400)
        self.assertEqual(self.client.get('/api/history?limit=oops').status_code,400)

    def test_disconnect_has_no_deadlock_and_sse_reports_offline(self):
        self.client.post('/api/telemetry',json=MESA)
        server.received = time.monotonic()-11
        self.assertFalse(self.client.get('/api/status').json['is_online'])
        response = self.client.get('/api/events', buffered=False)
        first = next(iter(response.response)).decode()
        self.assertIn('event: init',first)
        self.assertIn('"is_online": false',first)
        response.close()

    def test_sse_receives_new_telemetry(self):
        response = self.client.get('/api/events',buffered=False)
        iterator = iter(response.response)
        self.assertIn(b'event: init',next(iterator))
        self.client.post('/api/telemetria',json=MESA)
        with patch.object(server.time,'sleep'):
            self.assertIn(b'OPERANDO',next(iterator))
        response.close()

    def test_durable_history_after_server_state_reset(self):
        self.client.post('/api/telemetry',json=MESA)
        server.latest, server.received = {}, None
        self.assertEqual(self.client.get('/api/history').json['items'][0]['device_id'],'opta1')
        self.assertFalse(self.client.get('/api/status').json['is_online'])

    def test_frame_resynchronizes(self):
        frames=bridge.Frames()
        self.assertIsNone(frames.feed('CNC_CHUNK:CNC_JSON:{"lost":'))
        self.assertEqual(frames.feed('CNC_JSON:'+json.dumps(MESA)),MESA)


if __name__ == '__main__':
    unittest.main()
