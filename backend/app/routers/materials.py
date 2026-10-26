import re
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from ..database import get_repository
from ..material_storage import MaterialFileUnavailable, get_material_file_store
from ..services import now

router = APIRouter(prefix="/api/materials", tags=["과목별 교재"])
LOCAL_LIBRARY = Path(__file__).resolve().parents[3] / ".local" / "library"


class MaterialWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    subject: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=200)
    url: HttpUrl
    kind: str = Field(pattern=r"^(pdf|pptx|google_slides|canva|link)$")
    note: str = Field(default="", max_length=1000)

    @field_validator("url")
    @classmethod
    def secure_url(cls, value):
        if value.scheme != "https" or value.username or value.password:
            raise ValueError("로그인 정보가 포함되지 않은 https 교재 주소를 입력해 주세요.")
        return value


def subject_key(title):
    return re.sub(r"^20\d{2}\s+", "", title).strip()


@router.get("/subjects")
def subjects(repo=Depends(get_repository)):
    groups = {}
    for course in repo.list("courses"):
        title = subject_key(course.get("title", "교육"))
        group = groups.setdefault(title, {"subject": title, "course_count": 0, "hours": 0, "materials": []})
        group["course_count"] += 1
        group["hours"] += course.get("hours", 0)
    for material in repo.list("materials"):
        title = material["subject"]
        group = groups.setdefault(title, {"subject": title, "course_count": 0, "hours": 0, "materials": []})
        group["materials"].append(material)
    return {"items": sorted(groups.values(), key=lambda row: (-len(row["materials"]), -row["course_count"], row["subject"])),
            "matching_rule": "교육명 앞의 연도만 제거해 과목을 묶습니다. 다른 과목을 임의로 합치지 않습니다."}


@router.get("")
def list_materials(subject: str | None = Query(None, max_length=200), repo=Depends(get_repository)):
    return {"items": [row for row in repo.list("materials") if not subject or row["subject"] == subject]}


@router.post("", status_code=201)
def create_material(body: MaterialWrite, repo=Depends(get_repository)):
    stamp = now()
    return repo.save("materials", uuid4().hex, {**body.model_dump(mode="json"), "source_type": "link", "created_at": stamp, "updated_at": stamp, "deleted": False})


@router.delete("/{key}")
def delete_material(key: str, repo=Depends(get_repository)):
    if not repo.get("materials", key):
        raise HTTPException(404, "연결된 교재를 찾을 수 없습니다.")
    repo.soft_delete("materials", key, now())
    return {"id": key, "deleted": True}


@router.get("/{key}/file")
def material_file(key: str, download: bool = False, repo=Depends(get_repository)):
    record = repo.get("materials", key)
    if not record or record.get("source_type") not in {"local_file", "firestore_file"}:
        raise HTTPException(404, "교재 파일을 찾을 수 없습니다.")
    if record.get("source_type") == "firestore_file":
        try:
            target = get_material_file_store().get_file(record.get("storage_sha256"))
        except MaterialFileUnavailable as exc:
            raise HTTPException(503, str(exc)) from exc
        return FileResponse(target, media_type="application/pdf", filename=record.get("file_name", "교재.pdf"),
                            content_disposition_type="attachment" if download else "inline",
                            headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})
    root = LOCAL_LIBRARY.resolve()
    target = (root / record.get("storage_name", "")).resolve()
    if target.parent != root or not target.is_file() or target.suffix.lower() not in {".pdf", ".pptx"}:
        raise HTTPException(404, "교재 파일을 찾을 수 없습니다.")
    media = "application/pdf" if target.suffix.lower() == ".pdf" else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    return FileResponse(target, media_type=media, filename=record.get("file_name", target.name),
                        content_disposition_type="attachment" if download else "inline")


@router.get("/{key}/original")
def material_original(key: str, repo=Depends(get_repository)):
    record = repo.get('materials', key)
    if not record or not record.get('original_storage_sha256'):
        raise HTTPException(404, '연결된 PowerPoint 원본을 찾을 수 없습니다.')
    try:
        target = get_material_file_store().get_file(record['original_storage_sha256'], kind='pptx')
    except MaterialFileUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    return FileResponse(target,
                        media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
                        filename=record.get('original_file_name', '교재.pptx'),
                        content_disposition_type='attachment',
                        headers={'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff'})
