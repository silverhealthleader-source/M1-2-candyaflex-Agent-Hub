from collections import Counter

STATUS_LABELS = {"scheduled": "등록 계획", "held": "보류", "completed": "실시·승인 완료", "cancelled": "폐강 확정"}


def select_plans(rows, date_from=None, date_to=None):
    return sorted([row for row in rows if (not date_from or row["date"] >= str(date_from))
                   and (not date_to or row["date"] <= str(date_to))],
                  key=lambda row: (row["date"], row["start_time"], row["id"]))


def summarize_plans(rows):
    counts = Counter(row["status"] for row in rows)
    confirmed_zoom = [r for r in rows if r.get("replacement_status") == "confirmed"
                      and r.get("replacement_mode") == "온라인 Zoom"]
    pending_zoom = [r for r in confirmed_zoom if r.get("replacement_schedule_status") != "confirmed"
                    or not all(r.get(key) for key in ["replacement_date", "replacement_start_time", "replacement_end_time"])]
    return {"count": len(rows), "by_status": {key: counts[key] for key in STATUS_LABELS},
            "source_planned_hours": round(sum(r["planned_hours"] for r in rows), 2),
            "scheduled_hours": round(sum(r["planned_hours"] for r in rows if r["status"] == "scheduled"), 2),
            "held_hours": round(sum(r["planned_hours"] for r in rows if r["status"] == "held"), 2),
            "completed_plan_hours": round(sum(r["planned_hours"] for r in rows if r["status"] == "completed"), 2),
            "cancelled_plan_hours": round(sum(r["planned_hours"] for r in rows if r["status"] == "cancelled"), 2),
            "review_after": sorted({r["decision_review_after"] for r in rows if r.get("decision_review_after")}),
            "conditional_zoom_count": sum(bool(r.get("replacement_condition")) and r.get("replacement_status") != "confirmed" for r in rows),
            "confirmed_zoom_count": len(confirmed_zoom),
            "zoom_schedule_pending_count": len(pending_zoom),
            "note": "교육계획은 실적과 별도 집계합니다. 시간·인원은 원본 계획서 기준이며 실시·승인 상태와 별개입니다. "
                    "폐강된 원래 일정과 대체 수업을 구분합니다. 온라인 대체 확정 여부와 날짜·시간 확정 여부는 각각 확인합니다. "
                    "보류는 폐강 확정이 아니며 대체 수업의 실제 출석·시간·승인으로 집계하지 않습니다."}


def planning_context(rows):
    selected = select_plans(rows)
    return {**summarize_plans(selected), "sessions": [
        {key: row.get(key) for key in ["date", "start_time", "end_time", "institution", "region", "title", "status", "status_note", "approval_status", "planned_hours", "planned_students", "replacement_condition",
                                     "replacement_mode", "replacement_status", "replacement_schedule_status", "replacement_date", "replacement_start_time", "replacement_end_time", "replacement_note"]}
        for row in selected[:80]], "sessions_truncated": len(selected) > 80}
