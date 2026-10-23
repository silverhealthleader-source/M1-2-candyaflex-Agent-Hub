from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from app.database import get_repository
from app.main import app
from app.routers import chat
from app.services import ChatUnavailable, build_summary


class MemoryRepository:
    """Isolated test double only; the actual application always uses Firestore."""
    def __init__(self):
        self.tables = {"data": {}, "courses": {}, "conversations": {}, "materials": {}, "plans": {}}

    def list(self, collection):
        return [deepcopy(r) for r in self.tables[collection].values() if not r.get("deleted")]

    def get(self, collection, key):
        row = self.tables[collection].get(key)
        return deepcopy(row) if row and not row.get("deleted") else None

    def save(self, collection, key, value, merge=False):
        row = {**(self.tables[collection].get(key, {}) if merge else {}), **deepcopy(value), "id": key}
        self.tables[collection][key] = row
        return deepcopy(row)

    def soft_delete(self, collection, key, timestamp):
        self.tables[collection][key].update(deleted=True, updated_at=timestamp)


@pytest.fixture
def setup():
    repo = MemoryRepository()
    app.dependency_overrides[get_repository] = lambda: repo
    with TestClient(app) as client:
        yield client, repo
    app.dependency_overrides.clear()


def test_crud_summary_and_source_preservation(setup):
    client, repo = setup
    response = client.post("/api/data", json={"date": "2026-10-23", "value": 2, "memo": "실습", "students": 7})
    assert response.status_code == 201
    key = response.json()["id"]
    assert client.get("/api/data/summary").json()["students"]["total"] == 7
    assert client.put(f"/api/data/{key}", json={"value": 3}).status_code == 200
    assert client.get("/api/data/summary").json()["metrics"]["total"] == 3
    assert client.delete(f"/api/data/{key}").status_code == 200
    assert client.get("/api/data").json()["total"] == 0
    assert repo.tables["data"][key]["value"] == 3


@pytest.mark.parametrize("value", [-1, 25, "NaN", "Infinity"])
def test_invalid_hours_are_rejected(setup, value):
    client, _ = setup
    assert client.post("/api/data", json={"date": "2026-10-23", "value": value, "memo": "실습"}).status_code == 422


def test_invalid_date_range_and_missing_ids(setup):
    client, _ = setup
    assert client.get("/api/data/summary?date_from=2026-10-23&date_to=2026-01-01").status_code == 422
    assert client.put("/api/data/unknown", json={"memo": "변경"}).status_code == 404
    assert client.get("/api/conversations/unknown").status_code == 404


def test_course_students_are_counted_once_across_dates_and_time_slots_preserved():
    courses = [{"course_id": "a", "title": "같은 교육", "students_for_analysis": 5, "satisfaction_for_analysis": None},
               {"course_id": "b", "title": "같은 교육", "students_for_analysis": 6, "satisfaction_for_analysis": 100}]
    rows = [{"course_id": "a", "date": "2026-10-01", "value": 2},
            {"course_id": "a", "date": "2026-10-02", "value": 2},
            {"course_id": "b", "date": "2026-10-01", "value": 1}]
    result = build_summary(rows, courses)
    assert result["students"]["total"] == 11
    assert result["course_count"] == 2 and result["count"] == 3
    assert result["satisfaction"] == {"average": 100, "scored_courses": 1, "excluded_courses": 1}


def test_chat_injects_summary_and_autosaves_and_loads_full_history(setup, monkeypatch):
    client, repo = setup
    client.post("/api/data", json={"date": "2026-10-23", "value": 2, "memo": "교육"})
    captured = []
    def fake_answer(summary, messages):
        captured.append((summary, deepcopy(messages)))
        return f"기록된 교육시간은 {summary['metrics']['total']}시간입니다."
    monkeypatch.setattr(chat, "generate_answer", fake_answer)
    first = client.post("/api/chat", json={"message": "교육시간을 알려줘"})
    assert first.status_code == 200 and first.json()["saved"]
    key = first.json()["conversation_id"]
    second = client.post("/api/chat", json={"message": "기준일도 알려줘", "conversation_id": key})
    assert second.status_code == 200
    assert len(captured[1][1]) == 3 and captured[0][0]["metrics"]["total"] == 2
    assert len(client.get(f"/api/conversations/{key}").json()["messages"]) == 4
    assert not client.get("/api/conversations").json()["messages_included"]


def test_failed_ai_call_is_not_saved_as_success(setup, monkeypatch):
    client, repo = setup
    def fail(summary, messages):
        raise ChatUnavailable("API 연결 필요")
    monkeypatch.setattr(chat, "generate_answer", fail)
    assert client.post("/api/chat", json={"message": "안녕"}).status_code == 503
    assert not repo.list("conversations")




def test_calendar_keeps_distinct_time_slots_and_uses_edited_hours(setup):
    client, repo = setup
    for key, start, end, hours in [("morning", "09:00", "11:00", 3), ("afternoon", "14:00", "16:00", 2)]:
        repo.save("data", key, {"date": "2026-10-01", "course_title": "같은 교육명", "value": hours,
                  "edited": key == "morning", "schedule_units": [{"start_time": start, "end_time": end, "hours": 2, "topic": "실습"}]})
    repo.save("data", "previous-year", {"date": "2025-10-01", "value": 7})
    result = client.get("/api/data/calendar?year=2026").json()
    assert result["available_years"] == [2026, 2025] and len(result["months"]) == 12
    assert result["hours"] == 5 and result["record_count"] == 2
    october = result["months"][9]
    assert october["hours"] == 5 and october["day_count"] == 1
    assert [r["id"] for r in october["days"][0]["records"]] == ["morning", "afternoon"]
    assert october["days"][0]["records"][0]["schedule_units"][0]["hours"] == 2
    assert result["months"][0]["has_records"] is False
    assert client.get("/api/data/calendar?year=1999").status_code == 422


def test_material_links_group_with_exact_subject_and_can_be_removed(setup):
    client, repo = setup
    repo.save("courses", "a", {"title": "2026 이미지 생성", "hours": 2})
    repo.save("courses", "b", {"title": "2025 이미지 생성", "hours": 3})
    repo.save("courses", "c", {"title": "이미지 편집", "hours": 1})
    body = {"subject": "이미지 생성", "title": "실습 교재", "kind": "canva", "url": "https://www.canva.com/d/example"}
    response = client.post("/api/materials", json=body)
    assert response.status_code == 201
    key = response.json()["id"]
    groups = client.get("/api/materials/subjects").json()["items"]
    assert len(groups) == 2 and groups[0]["subject"] == "이미지 생성"
    assert groups[0]["course_count"] == 2 and groups[0]["hours"] == 5
    assert len(groups[0]["materials"]) == 1
    assert client.get("/api/materials?subject=이미지 편집").json()["items"] == []
    assert client.delete(f"/api/materials/{key}").status_code == 200
    assert not client.get("/api/materials").json()["items"]
    assert repo.tables["materials"][key]["deleted"] is True


@pytest.mark.parametrize("url", ["javascript:alert(1)", "http://example.com/teaching.pdf", "https://user:secret@example.com/teaching.pdf"])
def test_material_rejects_unsafe_links(setup, url):
    client, _ = setup
    assert client.post("/api/materials", json={"subject": "교육", "title": "교재", "kind": "pdf", "url": url}).status_code == 422


def test_local_material_serves_only_registered_files_inside_library(setup, monkeypatch, tmp_path):
    from app.routers import materials
    client, repo = setup
    library = tmp_path / "library"
    library.mkdir()
    pdf_bytes = b"%PDF-1.4 registered teaching file"
    (library / "registered.pdf").write_bytes(pdf_bytes)
    (tmp_path / "outside.pdf").write_bytes(b"private unrelated file")
    monkeypatch.setattr(materials, "LOCAL_LIBRARY", library)
    repo.save("materials", "good", {"source_type": "local_file", "storage_name": "registered.pdf", "file_name": "slides.pdf"})
    repo.save("materials", "bad", {"source_type": "local_file", "storage_name": "../outside.pdf"})
    response = client.get("/api/materials/good/file")
    assert response.content == pdf_bytes and response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].startswith("inline;")
    assert client.get("/api/materials/good/file?download=true").headers["content-disposition"].startswith("attachment;")
    assert client.get("/api/materials/bad/file").status_code == 404
    assert client.get("/api/materials/unknown/file").status_code == 404


def test_report_agent_uses_its_role_and_separate_history(setup, monkeypatch):
    client, repo = setup
    captured = []
    def fake_answer(summary, messages):
        captured.append(summary["agent_id"])
        return "강사 활동 보고서 초안"
    monkeypatch.setattr(chat, "generate_answer", fake_answer)
    response = client.post("/api/chat", json={"message": "보고서를 만들어 줘", "agent_id": "report"})
    assert response.status_code == 200 and captured == ["report"]
    key = response.json()["conversation_id"]
    assert client.get(f"/api/conversations/{key}").json()["agent_id"] == "report"
    assert client.get("/api/conversations").json()["items"][0]["agent_id"] == "report"
    assert client.post("/api/chat", json={"message": "이어서 분석", "agent_id": "analysis", "conversation_id": key}).status_code == 409
    assert client.post("/api/chat", json={"message": "계속 작성", "agent_id": "report", "conversation_id": key}).status_code == 200








