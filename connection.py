"""
Centraliza a conexão com o MongoDB e o acesso às collections.

Decisão de configuração (V1): sem .env, sem Docker. A URL e o nome do banco
possuem um valor padrão direto no código, mas podem ser sobrescritos por
variáveis de ambiente (MONGO_URL / MONGO_DB_NAME) caso necessário -- por
exemplo, para rodar os testes automatizados com um MongoDB isolado em
memória (MONGO_TEST=1), sem precisar de um servidor MongoDB real.
"""

import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("MONGO_DB_NAME", "cnc_monitor")

if os.getenv("MONGO_TEST") == "1":
    # Usado apenas pelos testes automatizados: banco MongoDB em memória,
    # sem depender de um servidor MongoDB real rodando na máquina de CI/dev.
    import mongomock

    client = mongomock.MongoClient()
else:
    from pymongo import MongoClient

    client = MongoClient(MONGO_URL)

db = client[DATABASE_NAME]

cncs_collection = db["cncs"]
devices_collection = db["devices"]
telemetry_collection = db["telemetry"]


def create_indexes() -> None:
    """Cria apenas os índices realmente úteis para as consultas da V1."""
    cncs_collection.create_index("code", unique=True)
    devices_collection.create_index("code", unique=True)
    devices_collection.create_index("mac_address", unique=True)
    devices_collection.create_index("cnc_id")
    telemetry_collection.create_index("device_id")
    telemetry_collection.create_index("timestamp")


def check_connection() -> None:
    """Levanta exceção se o MongoDB não estiver acessível."""
    client.admin.command("ping")
