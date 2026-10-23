import json
import os
from functools import lru_cache
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore
from google.auth.credentials import AnonymousCredentials
from google.cloud.firestore import Client

from .config import get_settings


class DatabaseNotConfigured(RuntimeError):
    pass


@lru_cache
def get_db():
    settings = get_settings()
    if not settings.database_configured:
        raise DatabaseNotConfigured("Firebase 연결 설정이 필요합니다. 먼저 Firestore와 서비스 계정 연결을 완료해 주세요.")
    if settings.emulator_host:
        if settings.environment == "production":
            raise DatabaseNotConfigured("운영 환경에서는 로컬 에뮬레이터를 사용할 수 없습니다.")
        return Client(project=settings.project_id, credentials=AnonymousCredentials())
    # The SDK treats a present-but-empty variable as an emulator endpoint.
    if os.environ.get("FIRESTORE_EMULATOR_HOST") == "":
        os.environ.pop("FIRESTORE_EMULATOR_HOST", None)
    try:
        raw = settings.service_account.strip()
        certificate = json.loads(raw) if raw.startswith("{") else str(Path(raw or settings.credentials_path).expanduser())
        try:
            app = firebase_admin.get_app("candy-a-academy")
        except ValueError:
            app = firebase_admin.initialize_app(credentials.Certificate(certificate), {"projectId": settings.project_id}, name="candy-a-academy")
        if app.project_id != settings.project_id:
            raise DatabaseNotConfigured("설정된 Firebase 프로젝트와 인증 정보의 프로젝트가 다릅니다.")
        return firestore.client(app)
    except DatabaseNotConfigured:
        raise
    except Exception as exc:
        raise DatabaseNotConfigured("Firebase 인증 파일을 읽을 수 없습니다. 파일 경로와 프로젝트 설정을 확인해 주세요.") from exc


class Repository:
    def __init__(self, db):
        self.db = db

    def list(self, collection):
        return [{**doc.to_dict(), "id": doc.id} for doc in self.db.collection(collection).stream(timeout=15, retry=None) if not (doc.to_dict() or {}).get("deleted", False)]

    def get(self, collection, key):
        doc = self.db.collection(collection).document(key).get(timeout=15, retry=None)
        if not doc.exists or (doc.to_dict() or {}).get("deleted", False):
            return None
        return {**doc.to_dict(), "id": doc.id}

    def save(self, collection, key, value, merge=False):
        self.db.collection(collection).document(key).set(value, merge=merge, timeout=15, retry=None)
        return {**value, "id": key}

    def soft_delete(self, collection, key, timestamp):
        self.db.collection(collection).document(key).update({"deleted": True, "updated_at": timestamp}, timeout=15, retry=None)


def get_repository():
    return Repository(get_db())
