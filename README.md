# SCOMPTEC CNC Monitor — Backend V1

Backend para monitoramento de máquinas CNC industriais. Um gateway ESP32
instalado no gabinete elétrico da CNC observa sinais existentes da máquina e
os envia via Wi-Fi/HTTP para este backend, que os armazena no MongoDB.

```text
CNC → Interface de aquisição → ESP32 Gateway → Backend (FastAPI) → MongoDB
```

O sistema **não** envia comandos para a CNC — apenas observa e registra.

---

## 1. Arquitetura

```text
cnc-monitor/
├── app/
│   ├── main.py                  # cria o FastAPI app, inclui routers, /health
│   ├── database/
│   │   └── connection.py        # cliente MongoDB, collections, índices
│   ├── schemas/                 # Pydantic: validação de entrada/saída
│   │   ├── cnc.py
│   │   ├── device.py
│   │   └── telemetry.py
│   ├── services/                # regras de negócio (acessam o MongoDB)
│   │   ├── cnc_service.py
│   │   ├── device_service.py
│   │   └── telemetry_service.py
│   └── routers/                 # endpoints HTTP (chamam os services)
│       ├── cnc.py
│       ├── devices.py
│       └── telemetry.py
├── tests/
│   ├── conftest.py
│   ├── test_cnc.py
│   ├── test_devices.py
│   └── test_telemetry.py
├── requirements.txt
└── README.md
```

Não há uma pasta `models/` com classes ODM: como o MongoDB é usado sem um
mapeamento objeto-documento formal, os documentos são `dict`s simples e os
`schemas/` Pydantic já cobrem toda a validação necessária para a V1. Isso
evita uma camada extra que apenas espelharia os schemas sem agregar valor.

### Decisões de design importantes

- **Identificadores**: cada CNC/Device/Telemetry usa um **UUID como `_id`**
  do MongoDB (em vez do `ObjectId` padrão). Isso mantém a API independente
  de detalhes internos do Mongo, sem precisar manter dois campos (`_id` e
  `id`) sincronizados — o UUID *é* o `_id`.
- **Código amigável** (`CNC01`, `DVC01`, ...): gerado contando os documentos
  existentes e avançando até achar um código livre; colisões concorrentes
  são resolvidas com retry sobre o índice único de `code`. Simples e
  suficiente para o ritmo de cadastro esperado numa V1 (não há
  auto-incremento nativo no MongoDB).
- **`online` (device) não é armazenado**: é sempre calculado a partir de
  `last_seen` no momento da leitura (`agora - last_seen <= 5s`). Evitar
  armazenar esse campo evita que ele fique dessincronizado do `last_seen`.
- **Transição da CNC para `UNKNOWN`**: como esta V1 não tem agendador de
  tarefas em background, a transição é feita de forma "preguiçosa" — toda
  vez que `GET /cncs/{id}/status` é chamado, se o gateway estiver offline e
  o status salvo ainda não for `UNKNOWN`, o backend registra a transição
  antes de responder.
- **Exclusão em cascata manual**: o MongoDB não tem `ON DELETE CASCADE`.
  Ao excluir uma CNC, o backend exclui também os Devices associados e as
  Telemetrias desses Devices, para não deixar referências quebradas.

---

## 2. Requisitos

- Python 3.11+
- MongoDB rodando localmente (`mongodb://localhost:27017`)

---

## 3. Instalação

```bash
git clone <repo>
cd cnc-monitor
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 4. Configuração do MongoDB

Não há `.env` nesta V1. A conexão usa por padrão:

```text
MONGO_URL     = mongodb://localhost:27017
MONGO_DB_NAME = cnc_monitor
```

Esses valores podem ser sobrescritos por variável de ambiente, se
necessário, mas isso é opcional — o projeto funciona com um MongoDB local
padrão sem nenhuma configuração adicional. O banco e as collections
(`cncs`, `devices`, `telemetry`) e seus índices são criados automaticamente
na inicialização do FastAPI.

**Iniciar o MongoDB local:**

```bash
# Linux (serviço já instalado)
sudo systemctl start mongod

# ou diretamente
mongod --dbpath /caminho/para/dados
```

---

## 5. Executar o backend

```bash
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

---

## 6. Exemplos de uso

### 6.1 Criar uma CNC

```bash
curl -X POST http://localhost:8000/cncs \
  -H "Content-Type: application/json" \
  -d '{"name": "Centro de Usinagem 01", "description": "Máquina utilizada para testes"}'
```

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/cncs `
  -ContentType "application/json" `
  -Body '{"name": "Centro de Usinagem 01", "description": "Máquina utilizada para testes"}'
```

Resposta: CNC criada com `code: "CNC01"`.

### 6.2 Registro automático da ESP32

```bash
curl -X POST http://localhost:8000/devices/register \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "A4:CF:12:8B:34:91",
    "ip_address": "192.168.1.37",
    "firmware_version": "1.0.0",
    "name": "Gateway ESP32"
  }'
```

Se o MAC já existir, o Device é apenas atualizado (IP, firmware, `last_seen`)
— nunca duplicado. Um Device novo nasce **sem** `cnc_id` (a associação é
manual, feita pelo administrador).

### 6.3 Associar Device → CNC

```bash
curl -X PUT http://localhost:8000/devices/{device_id} \
  -H "Content-Type: application/json" \
  -d '{"cnc_id": "UUID_DA_CNC"}'
```

### 6.4 Enviar telemetria

```bash
curl -X POST http://localhost:8000/devices/{device_id}/telemetry \
  -H "Content-Type: application/json" \
  -d '{
    "machine_active": true,
    "voltage_24v": true,
    "digital_signals": {"D01": true, "D02": false},
    "analog_signals": {"A01": 3.42},
    "extra_signals": {"cycle": true, "alarm": false, "emergency": false}
  }'
```

`timestamp` é opcional (horário de coleta do ESP32); `received_at` é sempre
o horário do servidor no momento do recebimento.

### 6.5 Consultar status da CNC

```bash
curl http://localhost:8000/cncs/{cnc_id}/status
```

```json
{
  "id": "UUID",
  "code": "CNC01",
  "name": "Centro de Usinagem 01",
  "status": "ACTIVE",
  "status_since": "2026-09-01T20:00:00",
  "status_duration_seconds": 843,
  "last_seen": "2026-09-01T20:14:03",
  "gateway_online": true,
  "device_code": "DVC01",
  "digital_signals": {"D01": true, "D02": false},
  "analog_signals": {"A01": 3.42},
  "voltage_24v": true
}
```

### 6.6 Consultar histórico

```bash
curl "http://localhost:8000/cncs/{cnc_id}/history?page=1&limit=50"
```

Filtros opcionais: `start`, `end` (ISO 8601), `page`, `limit`.

### 6.7 Atualização e exclusão

```bash
# Atualizar CNC
curl -X PUT http://localhost:8000/cncs/{cnc_id} -H "Content-Type: application/json" -d '{"name": "Novo nome"}'

# Excluir CNC (remove também Devices e Telemetrias associados)
curl -X DELETE http://localhost:8000/cncs/{cnc_id}

# Excluir Device
curl -X DELETE http://localhost:8000/devices/{device_id}
```

---

## 7. Endpoints implementados

### CNC
```text
POST   /cncs
GET    /cncs
GET    /cncs/{cnc_id}
PUT    /cncs/{cnc_id}
DELETE /cncs/{cnc_id}
GET    /cncs/{cnc_id}/status
GET    /cncs/{cnc_id}/history
```

### Devices
```text
POST   /devices/register
GET    /devices
GET    /devices/{device_id}
PUT    /devices/{device_id}
DELETE /devices/{device_id}
GET    /devices/{device_id}/status
```

### Telemetry
```text
POST /devices/{device_id}/telemetry
```

---

## 8. Executar os testes

Os testes usam `mongomock` (MongoDB em memória), então **não** exigem um
MongoDB real rodando:

```bash
pytest
```

`tests/conftest.py` define `MONGO_TEST=1` antes de importar a aplicação,
fazendo com que `app/database/connection.py` use o banco em memória
automaticamente.
