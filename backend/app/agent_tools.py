"""Read-only summary tool shared by GPT and the optional MCP adapter."""

SUMMARY_TOOL = {
    "type": "function",
    "name": "get_data_summary",
    "description": "현재 선택한 분석 기간의 교육기록 건수·시간·인원·통계·추세를 서버 계산값으로 다시 확인합니다. 교육계획은 실적과 구분합니다.",
    "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
    "strict": True,
}


def summary_for_tool(summary):
    result = {key: summary[key] for key in [
        "period", "count", "course_count", "teaching_days", "metrics", "students",
        "satisfaction", "trend", "monthly", "by_mode", "approval", "notes",
    ] if key in summary}
    if "planning" in summary:
        result["planning"] = {key: value for key, value in summary["planning"].items()
                              if key not in {"sessions", "sessions_truncated"}}
    return result


def run_summary_tool(name, arguments, summary):
    if name != SUMMARY_TOOL["name"] or arguments != {}:
        raise ValueError("허용하지 않은 도구 요청입니다.")
    return summary_for_tool(summary)


class AgentAnswer(str):
    def __new__(cls, value, tool_calls):
        instance = super().__new__(cls, value)
        instance.tool_calls = tool_calls
        return instance
