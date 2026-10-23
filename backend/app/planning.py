from collections import Counter

STATUS_LABELS = {"scheduled": "등록 계획", "held": "보류", "completed": "실시·승인 완료", "cancelled": "폐강 확정"}


def select_plans(rows, date_from=None, date_to=None):
    return sorted([row for row in rows if (not date_from or row["date"] >= str(date_from))
                   and (not date_to or row["date"] <= str(date_to))],
                  key=lambda row: (row["date"], row["start_time"], row["id"]))


def summarize_plans(rows):
    counts = Counter(row["status"] for row in rows)
    return {"count": len(rows), "by_status": {key: counts[key] for key in STATUS_LABELS},
            "source_planned_hours": round(sum(r["planned_hours"] for r in rows), 2),
            "scheduled_hours": round(sum(r["planned_hours"] for r in rows if r["status"] == "scheduled"), 2),
            "held_hours": round(sum(r["planned_hours"] for r in rows if r["status"] == "held"), 2),
            "completed_plan_hours": round(sum(r["planned_hours"] for r in rows if r["status"] == "completed"), 2),
            "review_after": sorted({r["decision_review_after"] for r in rows if r.get("decision_review_after")}),
            "conditional_zoom_count": sum(bool(r.get("replacement_condition")) for r in rows),
            "note": "교육계획은 실적과 별도 집계합니다. 시간·인원은 계획서 기준이며 실시·승인 상태와 별개입니다. 보류는 폐강 확정이 아닙니다. 줌 대체 날짜·시간·인원은 미확정입니다."}


def planning_context(rows):
    selected = select_plans(rows)
    return {**summarize_plans(selected), "sessions": [
        {key: row.get(key) for key in ["date", "start_time", "end_time", "institution", "region", "title", "status", "approval_status", "planned_hours", "planned_students", "replacement_condition"]}
        for row in selected[:80]], "sessions_truncated": len(selected) > 80}
