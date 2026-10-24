from collections import defaultdict

from .planning import select_plans, summarize_plans, with_schedule_conflicts


def build_calendar(rows, year=None, plans=()):
    plans = with_schedule_conflicts(plans)
    all_years = {int(row["date"][:4]) for row in [*rows, *plans]}
    selected_year = year or max(all_years, default=2026)
    months = []
    for number in range(1, 13):
        key = f"{selected_year}-{number:02d}"
        records = [row for row in rows if row["date"].startswith(key)]
        days = defaultdict(list)
        for row in records:
            days[row["date"]].append({"id": row["id"], "title": row.get("course_title", "교육 기록"),
                "hours": row["value"], "mode": row.get("mode", "기타"), "venue": row.get("venue", ""),
                "memo": row.get("memo", ""), "source_file": row.get("source_file"),
                "edited": row.get("edited", False), "schedule_units": row.get("schedule_units", [])})
        day_list = []
        for date, entries in sorted(days.items()):
            entries.sort(key=lambda row: (min((u.get("start_time", "") for u in row["schedule_units"]), default="99:99"), row["id"]))
            day_list.append({"date": date, "hours": round(sum(row["hours"] for row in entries), 2),
                             "record_count": len(entries), "records": entries})
        month_plans = select_plans([row for row in plans if row["date"].startswith(key)])
        months.append({"month": key, "has_records": bool(records), "hours": round(sum(row["value"] for row in records), 2),
                       "record_count": len(records), "day_count": len(days), "days": day_list,
                       "plans": month_plans, "planning": summarize_plans(month_plans)})
    return {"year": selected_year, "available_years": sorted(all_years, reverse=True),
            "months": months, "record_count": sum(m["record_count"] for m in months),
            "hours": round(sum(m["hours"] for m in months), 2),
            "note": "기록이 없는 달은 교육 미실시로 단정하지 않습니다. 원본별 수업과 시간대를 모두 보존합니다."}
