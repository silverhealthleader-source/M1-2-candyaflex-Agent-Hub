from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from ..database import get_repository
from ..models import ConversationWrite
from ..services import now
from ..privacy import redact_text, redact_value

router = APIRouter(prefix="/api/conversations", tags=["대화 기록"])


@router.get("")
def list_conversations(repo=Depends(get_repository)):
    rows = sorted(repo.list("conversations"), key=lambda row: row.get("updated_at", ""), reverse=True)
    return {"items": [{k: row.get(k) for k in ["id", "title", "created_at", "updated_at", "agent_id"]} | {"message_count": len(row.get("messages", []))} for row in rows],
            "messages_included": False, "detail_endpoint": "/api/conversations/{id}"}


@router.get("/{key}")
def get_conversation(key: str, repo=Depends(get_repository)):
    row = repo.get("conversations", key)
    if not row:
        raise HTTPException(404, "대화를 찾을 수 없습니다.")
    return row


@router.post("", status_code=201)
def save_conversation(body: ConversationWrite, repo=Depends(get_repository)):
    existing = repo.get("conversations", body.id) if body.id else None
    if body.id and not existing:
        raise HTTPException(404, "저장할 대화를 찾을 수 없습니다.")
    stamp = now()
    messages = redact_value([m.model_dump() for m in body.messages])
    row = {"title": redact_text(body.title), "messages": messages, "agent_id": existing.get("agent_id", "analysis") if existing else "analysis",
           "created_at": existing.get("created_at", stamp) if existing else stamp, "updated_at": stamp, "deleted": False,
           "save_mode": "manual", "tool_calls": existing.get("tool_calls", []) if existing else [],
           "messages_edited_manually": bool(existing and existing.get("messages") != messages)}
    return repo.save("conversations", body.id or uuid4().hex, row)


@router.delete("/{key}")
def delete_conversation(key: str, repo=Depends(get_repository)):
    if not repo.get("conversations", key):
        raise HTTPException(404, "대화를 찾을 수 없습니다.")
    repo.soft_delete("conversations", key, now())
    return {"id": key, "deleted": True}
