import secrets
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from google.api_core.exceptions import GoogleAPICallError, ResourceExhausted

from .config import get_settings
from .database import DatabaseNotConfigured
from .routers import chat, conversations, data, materials, plans
from .services import ChatUnavailable

settings = get_settings()
app = FastAPI(title="캔디A플렉스 에듀 융합에이전트 API", version="0.2.1", description="교육운영 기록 분석과 데이터 기반 강사 AI 비서")
app.add_middleware(CORSMiddleware, allow_origins=list(settings.origins), allow_credentials=False,
                   allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Authorization", "Content-Type"])
bearer = HTTPBearer(auto_error=False)


def access(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    current = get_settings()
    if current.environment == "production" and not current.access_token:
        raise HTTPException(503, "개인 데이터 보호를 위한 APP_ACCESS_TOKEN 설정이 필요합니다.")
    if current.access_token and (not credentials or not secrets.compare_digest(credentials.credentials, current.access_token)):
        raise HTTPException(401, "접속 키를 확인해 주세요.", headers={"WWW-Authenticate": "Bearer"})


for router in [data.router, conversations.router, chat.router, materials.router, plans.router]:
    app.include_router(router, dependencies=[Depends(access)])


@app.get("/health", tags=["서비스 상태"])
def health():
    current = get_settings()
    return {"status": "ok", "database_configured": current.database_configured,
            "database_mode": "emulator" if current.emulator_host else "cloud", "ai_configured": bool(current.openai_key),
            "access_key_required": bool(current.access_token), "version": "0.2.1"}


@app.exception_handler(DatabaseNotConfigured)
def database_not_ready(request, exc):
    return JSONResponse(status_code=503, content={"detail": str(exc), "code": "DATABASE_NOT_READY"})


@app.exception_handler(ChatUnavailable)
def chat_not_ready(request, exc):
    return JSONResponse(status_code=503, content={"detail": str(exc), "code": "AI_NOT_READY"})


@app.exception_handler(GoogleAPICallError)
def database_connection_error(request, exc):
    return JSONResponse(status_code=503, content={"detail": "교육 데이터 저장소에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.", "code": "DATABASE_CONNECTION_FAILED"})


@app.exception_handler(ResourceExhausted)
def database_quota_error(request, exc):
    return JSONResponse(status_code=503, headers={"Retry-After": "60"},
                        content={"detail": "교육기록 저장소의 사용량 한도에 도달했습니다. 한도가 초기화된 뒤 다시 연결해 주세요. 연속 새로고침은 잠시 멈춰 주세요.",
                                 "code": "FIRESTORE_QUOTA_EXCEEDED"})


frontend = Path(__file__).resolve().parents[2] / "frontend"
if (frontend / "index.html").exists():
    app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
