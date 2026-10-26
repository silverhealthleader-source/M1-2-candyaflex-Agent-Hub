from fastapi import FastAPI
from fastapi.testclient import TestClient
from app import main
from app.config import Settings, get_settings


def test_production_does_not_publish_a_second_unguarded_frontend(monkeypatch):
    monkeypatch.setattr(main, "get_settings", lambda: Settings(environment="production"))
    application = FastAPI()
    main.mount_local_frontend(application)
    with TestClient(application) as client:
        for path in ["/", "/index.html", "/education.html", "/app.js", "/access/gate.mjs"]:
            assert client.get(path).status_code == 404


def test_local_frontend_remains_available_for_assignment_reproduction(monkeypatch):
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.setattr(main, "get_settings", lambda: Settings(environment="development"))
    application = FastAPI()
    main.mount_local_frontend(application)
    with TestClient(application) as client:
        assert client.get("/education.html").status_code == 200


def test_render_frontend_is_closed_even_if_development_is_misconfigured(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setattr(main, "get_settings", lambda: Settings(environment="development"))
    application = FastAPI()
    main.mount_local_frontend(application)
    with TestClient(application) as client:
        assert client.get("/index.html").status_code == 404


def test_render_defaults_to_production_without_an_explicit_app_env(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setenv("RENDER", "true")
    get_settings.cache_clear()
    try:
        assert get_settings().environment == "production"
    finally:
        get_settings.cache_clear()
