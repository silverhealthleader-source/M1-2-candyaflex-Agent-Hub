from typing import Literal

from fastapi import APIRouter, Depends, Query

from ..database import get_repository
from ..planning import select_plans, summarize_plans

router = APIRouter(prefix="/api/plans", tags=["등록 교육계획"])


@router.get("")
def list_plans(month: str | None = Query(None, pattern=r"^20\d{2}-(0[1-9]|1[0-2])$"),
               status: Literal["scheduled", "held", "completed", "cancelled"] | None = None,
               repo=Depends(get_repository)):
    rows = select_plans(repo.list("plans"))
    rows = [r for r in rows if (not month or r["date"].startswith(month)) and (not status or r["status"] == status)]
    return {"items": rows, "summary": summarize_plans(rows)}
