from datetime import date
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query

from ..database import get_repository
from ..models import DataCreate, DataUpdate
from ..services import build_summary, now, select_rows
from ..calendar import build_calendar
from ..planning import planning_context, select_plans

router = APIRouter(prefix="/api/data", tags=["교육 데이터"])


@router.get("/calendar")
def calendar(year: int | None = Query(None, ge=2000, le=2100), repo=Depends(get_repository)):
    return build_calendar(repo.list("data"), year, repo.list("plans"))


def filtered(repo, date_from, date_to, mode=None, search=None):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "시작일은 종료일보다 늦을 수 없습니다.")
    return select_rows(repo.list("data"), date_from, date_to, mode, search)


@router.get("/summary")
def summary(date_from: date | None = None, date_to: date | None = None, mode: str | None = None, repo=Depends(get_repository)):
    result = build_summary(filtered(repo, date_from, date_to, mode), repo.list("courses"))
    result["planning"] = planning_context(select_plans(repo.list("plans"), date_from, date_to))
    return result


@router.get("/export")
def export(date_from: date | None = None, date_to: date | None = None, repo=Depends(get_repository)):
    return {"exported_at": now(), "data": filtered(repo, date_from, date_to)}


@router.get("")
def list_data(date_from: date | None = None, date_to: date | None = None, mode: str | None = None,
              search: str | None = Query(None, max_length=200), limit: int = Query(30, ge=1, le=1000),
              offset: int = Query(0, ge=0), repo=Depends(get_repository)):
    rows = filtered(repo, date_from, date_to, mode, search)
    return {"items": rows[offset:offset + limit], "total": len(rows), "limit": limit, "offset": offset}


@router.post("", status_code=201)
def create_data(body: DataCreate, repo=Depends(get_repository)):
    stamp = now()
    row = {**body.model_dump(mode="json"), "unit": "hours", "created_at": stamp, "updated_at": stamp,
           "source": "manual", "approval_status": None, "deleted": False}
    return repo.save("data", uuid4().hex, row)


@router.put("/{key}")
def update_data(key: str, body: DataUpdate, repo=Depends(get_repository)):
    current = repo.get("data", key)
    if not current:
        raise HTTPException(404, "교육 기록을 찾을 수 없습니다.")
    changes = body.model_dump(mode="json", exclude_none=True, exclude_unset=True)
    if not changes:
        raise HTTPException(422, "수정할 항목을 입력해 주세요.")
    if current.get("course_id") and "students" in changes:
        raise HTTPException(422, "원본 과정의 인원은 과정 기록에서 관리합니다. 일자별로 중복 입력할 수 없습니다.")
    changes.update({"updated_at": now(), "edited": True})
    repo.save("data", key, changes, merge=True)
    return {**current, **changes}


@router.delete("/{key}")
def delete_data(key: str, repo=Depends(get_repository)):
    if not repo.get("data", key):
        raise HTTPException(404, "교육 기록을 찾을 수 없습니다.")
    repo.soft_delete("data", key, now())
    return {"id": key, "deleted": True}
