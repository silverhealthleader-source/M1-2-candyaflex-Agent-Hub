from types import SimpleNamespace

import pytest
from google.auth.credentials import AnonymousCredentials
from google.cloud.firestore import Client

from app import database
from app.config import Settings


@pytest.fixture(autouse=True)
def clear_database_cache():
    database.get_db.cache_clear()
    yield
    database.get_db.cache_clear()


@pytest.mark.parametrize("emulator_value", [None, ""])
def test_cloud_client_uses_google_endpoint_with_empty_or_absent_emulator(monkeypatch, emulator_value):
    if emulator_value is None:
        monkeypatch.delenv("FIRESTORE_EMULATOR_HOST", raising=False)
    else:
        monkeypatch.setenv("FIRESTORE_EMULATOR_HOST", emulator_value)
    settings = Settings(project_id="test-project", credentials_path="unused.json")
    monkeypatch.setattr(database, "get_settings", lambda: settings)
    monkeypatch.setattr(database.firebase_admin, "get_app", lambda name: SimpleNamespace(project_id="test-project"))
    monkeypatch.setattr(database.firestore, "client", lambda app: Client(project=app.project_id, credentials=AnonymousCredentials()))

    client = database.get_db()

    assert client._emulator_host is None
    assert client._target == "firestore.googleapis.com"


def test_development_emulator_endpoint_is_preserved(monkeypatch):
    monkeypatch.setenv("FIRESTORE_EMULATOR_HOST", "127.0.0.1:8088")
    monkeypatch.setattr(database, "get_settings", lambda: Settings(project_id="demo-test", emulator_host="127.0.0.1:8088"))
    assert database.get_db()._target == "127.0.0.1:8088"


def test_production_rejects_emulator(monkeypatch):
    monkeypatch.setattr(database, "get_settings", lambda: Settings(project_id="demo-test", emulator_host="127.0.0.1:8088", environment="production"))
    with pytest.raises(database.DatabaseNotConfigured, match="운영 환경"):
        database.get_db()
