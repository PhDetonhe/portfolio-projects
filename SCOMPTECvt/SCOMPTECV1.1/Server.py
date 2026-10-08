"""SCOMPTEC: recebe HTTP, normaliza sinais e persiste snapshots."""
import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from flask import Flask, Response, jsonify, request
from signals import normalize

ROOT = Path(__file__).resolve().parent
app = Flask(__name__, static_folder=str(ROOT / 'public'), static_url_path='/public')
app.config.update(MAX_CONTENT_LENGTH=16384, DATABASE=os.environ.get('SCOMPTEC_DB', str(ROOT / 'telemetria.sqlite3')))
lock = Lock()
# Nenhum arquivo ou thread é criado durante importação.
latest = {}
received = None
version = 0


def db():
    connection = sqlite3.connect(app.config['DATABASE'], timeout=5)
    connection.execute('CREATE TABLE IF NOT EXISTS telemetry (id INTEGER PRIMARY KEY, received TEXT NOT NULL, device TEXT NOT NULL, payload TEXT NOT NULL)')
    return connection


def snapshot():
    with lock:
        data = dict(latest)
        data['is_online'] = received is not None and time.monotonic() - received < 10
        return data, version


@app.get('/')
def index():
    return app.send_static_file('index.html')


@app.get('/health')
def health():
    return jsonify(ok=True)


@app.post('/api/telemetry')
@app.post('/api/telemetria')
def ingest():
    global latest, received, version
    try:
        data = normalize(request.get_json(silent=True))
    except ValueError as error:
        return jsonify(error=str(error)), 400
    data['recebido_em'] = data['last_updated'] = datetime.now(timezone.utc).isoformat()
    # Persistir antes de confirmar; falha de disco não gera sucesso falso.
    with lock:
        connection = db()
        try:
            with connection:
                connection.execute('INSERT INTO telemetry(received,device,payload) VALUES (?,?,?)',
                                   (data['recebido_em'], data['device_id'], json.dumps(data, allow_nan=False)))
        finally:
            connection.close()
        latest, received = data, time.monotonic()
        version += 1
    return jsonify(status='ok', received=data), 200


@app.get('/api/status')
def status():
    return jsonify(snapshot()[0])


@app.get('/api/history')
def history():
    try:
        limit = min(1000, max(1, int(request.args.get('limit', 100))))
    except ValueError:
        return jsonify(error='limit inválido'), 400
    connection = db()
    try:
        rows = connection.execute('SELECT payload FROM telemetry ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    finally:
        connection.close()
    return jsonify(items=[json.loads(row[0]) for row in reversed(rows)])


@app.get('/api/telemetria')
def legacy_status():
    # Envelope dos colegas; o payload mantém os nomes originais recebidos.
    records = history()
    if isinstance(records, tuple):
        return records
    return jsonify(latest=snapshot()[0], history=records.get_json()['items'], events=[])


@app.get('/api/events')
def events():
    def stream():
        previous = None
        while True:
            data, number = snapshot()
            key = (number, data['is_online'])
            if key != previous:
                event = 'init' if previous is None else 'telemetry'
                yield f'event: {event}\ndata: {json.dumps({"latest": data})}\n\n'
                previous = key
            else:
                yield ': keep-alive\n\n'
            time.sleep(1)
    return Response(stream(), mimetype='text/event-stream', headers={'Cache-Control':'no-cache', 'X-Accel-Buffering':'no'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8080'))
    print(f'SCOMPTEC: http://localhost:{port} | POST /api/telemetria', flush=True)
    app.run(host='0.0.0.0', port=port, threaded=True, debug=False)
