"""Validate local JSON and optionally create missing Firestore documents.

Usage: python scripts/import_data.py --apply
Existing IDs (including soft-deleted ones) are never overwritten or resurrected.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.database import get_db
from app.models import DataCreate
from app.services import now


def load_and_validate(folder):
    courses = json.loads((folder / "course_records.json").read_text(encoding="utf-8"))
    data = json.loads((folder / "data_records.json").read_text(encoding="utf-8"))
    ids = {row["course_id"] for row in courses}
    if len(ids) != len(courses) or len({r["id"] for r in data}) != len(data):
        raise ValueError("중복 ID가 있습니다. 원본별 식별자를 확인해 주세요.")
    for row in data:
        DataCreate.model_validate({k: row[k] for k in ["date", "value", "memo", "course_title", "mode", "venue"]})
        if row["course_id"] not in ids:
            raise ValueError("연결된 과정 정보가 없는 교육일 기록이 있습니다.")
    if abs(sum(r["hours"] for r in courses) - sum(r["value"] for r in data)) > 0.001:
        raise ValueError("과정 교육시간과 교육일별 교육시간 합계가 다릅니다.")
    return courses, data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="실제 연결된 Firestore에 없는 ID만 저장")
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parents[2] / "data")
    args = parser.parse_args()
    courses, data = load_and_validate(args.data_dir)
    report = {"validated_at": now(), "courses": len(courses), "data": len(data),
              "hours": sum(row["value"] for row in data), "applied": False}
    if not args.apply:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    db, settings = get_db(), get_settings()
    stamp = now()
    receipts = {}
    for collection, rows, id_field in [("courses", courses, "course_id"), ("data", data, "id")]:
        existing = {doc.id for doc in db.collection(collection).stream(timeout=20, retry=None)}
        missing = [row for row in rows if row[id_field] not in existing]
        for offset in range(0, len(missing), 200):
            batch = db.batch()
            for row in missing[offset:offset + 200]:
                document = {**row, "created_at": stamp, "updated_at": stamp, "deleted": False, "source": "pdf_import"}
                batch.create(db.collection(collection).document(row[id_field]), document)
            batch.commit(timeout=30, retry=None)
        expected_ids = {row[id_field] for row in rows}
        stored = [doc.to_dict() for doc in db.collection(collection).stream(timeout=20, retry=None) if doc.id in expected_ids]
        if len(stored) != len(expected_ids):
            raise RuntimeError(f"{collection}: 저장 후 문서 수가 맞지 않습니다.")
        receipts[collection] = {"created": len(missing), "existing_preserved": len(rows) - len(missing), "verified": len(stored)}
        if collection == "data":
            receipts[collection]["stored_hours_including_existing_edits"] = sum(row["value"] for row in stored)
    report.update({"applied": True, "project_id": settings.project_id,
                   "destination": "local_firestore_emulator" if settings.emulator_host else "cloud_firestore",
                   "collections": receipts})
    receipt_dir = Path(__file__).resolve().parents[2] / ".local"
    receipt_dir.mkdir(exist_ok=True)
    (receipt_dir / "import-receipt.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
