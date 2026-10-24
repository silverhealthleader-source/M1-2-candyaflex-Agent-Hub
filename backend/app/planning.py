from collections import Counter

STATUS_LABELS = {"scheduled": "등록 계획", "held": "보류", "completed": "실시·승인 완료", "cancelled": "폐강 확정"}


def is_confirmed_online(row):
    return row.get("schedule_status") == "confirmed" and row.get("delivery_mode") == "온라인 Zoom" and row.get("status") == "scheduled"


def with_schedule_conflicts(rows):
    result = [{**row, "schedule_conflicts": []} for row in rows]
    active = [row for row in result if row.get("status") == "scheduled"]
    for index, first in enumerate(active):
        for second in active[index + 1:]:
            if not (is_confirmed_online(first) or is_confirmed_online(second)):
                continue
            if first["date"] == second["date"] and first["start_time"] < second["end_time"] and second["start_time"] < first["end_time"]:
                for row, other in [(first, second), (second, first)]:
                    separate = (row.get("distinct_session_confirmed") is True and other.get("distinct_session_confirmed") is True
                                and row.get("same_time_separate_session_id") == other["id"]
                                and other.get("same_time_separate_session_id") == row["id"])
                    row["schedule_conflicts"].append({**{key: other.get(key) for key in ["id", "date", "start_time", "end_time", "title", "institution"]},
                                                      "distinct_session_confirmed": separate})
    return result


def select_plans(rows, date_from=None, date_to=None):
    return sorted([row for row in rows if (not date_from or row["date"] >= str(date_from))
                   and (not date_to or row["date"] <= str(date_to))],
                  key=lambda row: (row["date"], row["start_time"], row["id"]))


def summarize_plans(rows):
    rows = with_schedule_conflicts(rows)
    counts = Counter(row["status"] for row in rows)
    confirmed_zoom = [r for r in rows if r.get("replacement_status") == "confirmed"
                      and r.get("replacement_mode") == "온라인 Zoom"]
    grouped_zoom = [r for r in confirmed_zoom if r.get("replacement_schedule_status") == "group_confirmed" and r.get("replacement_schedule_group_id")]
    pending_zoom = [r for r in confirmed_zoom if r not in grouped_zoom and
                    (r.get("replacement_schedule_status") != "confirmed" or not all(r.get(key) for key in ["replacement_date", "replacement_start_time", "replacement_end_time"]))]
    online = [r for r in rows if is_confirmed_online(r)]
    months = sorted({r["date"][:7] for r in online})
    conflicts = {tuple(sorted([r["id"], other["id"]])) for r in rows for other in r["schedule_conflicts"]}
    confirmed_distinct = {tuple(sorted([r["id"], other["id"]])) for r in rows for other in r["schedule_conflicts"] if other["distinct_session_confirmed"]}
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
            "zoom_group_schedule_confirmed_count": len(grouped_zoom),
            "confirmed_online_count": len(online),
            "confirmed_online_hours": round(sum(r["planned_hours"] for r in online), 2),
            "online_schedule_monthly": [{"month": month, "count": sum(r["date"].startswith(month) for r in online),
                                          "hours": round(sum(r["planned_hours"] for r in online if r["date"].startswith(month)), 2)} for month in months],
            "schedule_conflict_count": len(conflicts),
            "confirmed_distinct_overlap_count": len(confirmed_distinct),
            "schedule_conflict_pending_count": len(conflicts - confirmed_distinct),
            "note": "교육계획은 실적과 별도 집계합니다. 시간·인원은 원본 계획서 기준이며 실시·승인 상태와 별개입니다. "
                    "폐강된 원래 일정과 대체 수업을 구분합니다. 온라인 대체 확정 여부와 날짜·시간 확정 여부는 각각 확인합니다. "
                    "보류는 폐강 확정이 아니며 대체 수업의 실제 출석·시간·승인으로 집계하지 않습니다."}


def planning_context(rows):
    selected = select_plans(with_schedule_conflicts(rows))
    return {**summarize_plans(selected), "sessions": [
        {key: row.get(key) for key in ["id", "date", "start_time", "end_time", "institution", "region", "title", "status", "status_note", "approval_status", "planned_hours", "planned_students", "replacement_condition",
                                     "replacement_mode", "replacement_status", "replacement_schedule_status", "replacement_date", "replacement_start_time", "replacement_end_time", "replacement_note",
                                     "replacement_schedule_group_id", "schedule_group_id", "schedule_status", "delivery_mode", "registration_status", "schedule_conflicts",
                                     "distinct_session_confirmed", "same_time_separate_session_id", "original_schedule_date"]}
        for row in selected[:80]], "sessions_truncated": len(selected) > 80}
