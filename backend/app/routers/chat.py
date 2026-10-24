from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from ..database import get_repository
from ..models import ChatRequest
from ..services import build_summary, generate_answer, now, select_rows
from ..planning import planning_context, select_plans

router = APIRouter(prefix="/api", tags=["강사 AI 비서"])


@router.post("/chat")
def chat(body: ChatRequest, repo=Depends(get_repository)):
    if body.date_from and body.date_to and body.date_from > body.date_to:
        raise HTTPException(422, "분석 기간을 확인해 주세요.")
    existing = repo.get("conversations", body.conversation_id) if body.conversation_id else None
    if body.conversation_id and not existing:
        raise HTTPException(404, "이전 대화를 찾을 수 없습니다.")
    if existing and existing.get("agent_id", "analysis") != body.agent_id:
        raise HTTPException(409, "담당 에이전트가 다른 대화입니다. 새 대화를 시작해 주세요.")
    history = existing.get("messages", []) if existing else []
    if len(history) >= 98:
        raise HTTPException(422, "새 대화를 시작해 주세요. 한 대화는 최대 50회 질문까지 저장합니다.")
    messages = history + [{"role": "user", "content": body.message}]
    summary = build_summary(select_rows(repo.list("data"), body.date_from, body.date_to), repo.list("courses"))
    summary["planning"] = planning_context(select_plans(repo.list("plans"), body.date_from, body.date_to))
    summary["agent_id"] = body.agent_id
    generated = generate_answer(summary, messages)
    tool_calls = getattr(generated, "tool_calls", [])
    answer = str(generated)
    messages.append({"role": "assistant", "content": answer})
    stamp, key = now(), body.conversation_id or uuid4().hex
    row = {"title": existing["title"] if existing else body.message[:50], "messages": messages, "agent_id": body.agent_id,
           "created_at": existing.get("created_at", stamp) if existing else stamp, "updated_at": stamp, "deleted": False,
           "tool_calls": (existing.get("tool_calls", []) if existing else []) + tool_calls}
    repo.save("conversations", key, row)
    return {"answer": answer, "conversation_id": key, "saved": True, "data_period": summary["period"], "data_count": summary["count"],
            "tool_calls": tool_calls}
