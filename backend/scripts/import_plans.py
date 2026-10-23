"""Import plan documents separately from historical results; preserve existing records."""
import argparse
from datetime import date, datetime
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.database import get_db
from app.planning import summarize_plans
from app.services import now


def validate(rows):
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("계획 ID가 중복되었습니다.")
    for row in rows:
        date.fromisoformat(row["date"])
        start, end = [datetime.strptime(row[key], "%H:%M") for key in ["start_time", "end_time"]]
        hours = (end - start).total_seconds() / 3600
        if not 0 < hours <= 24 or abs(hours - row["planned_hours"]) > 0.001:
            raise ValueError("계획 시간과 시작·종료 시간이 다릅니다.")
        if row["status"] not in {"scheduled", "held", "completed", "cancelled"}:
            raise ValueError("알 수 없는 계획 상태입니다.")
        if row["approval_status"] == "approved" and row["status"] != "completed":
            raise ValueError("실시·승인 완료 표시를 확인해 주세요.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, default=Path(__file__).resolve().parents[2] / "data" / "plan_records.json")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    rows = json.loads(args.file.read_text(encoding="utf-8"))
    validate(rows)
    receipt = {"validated_at": now(), **summarize_plans(rows), "applied": False}
    if args.apply:
        db = get_db()
        existing = {doc.id for doc in db.collection("plans").stream(timeout=20, retry=None)}
        missing = [r for r in rows if r["id"] not in existing]
        for offset in range(0, len(missing), 200):
            batch = db.batch()
            for row in missing[offset:offset + 200]:
                batch.create(db.collection("plans").document(row["id"]), {**row, "created_at": now(), "updated_at": now(), "deleted": False})
            batch.commit(timeout=30, retry=None)
        receipt.update(applied=True, created=len(missing), existing_preserved=len(rows) - len(missing))
        target = Path(__file__).resolve().parents[2] / ".local" / "plans-import.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
