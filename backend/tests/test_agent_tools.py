from types import SimpleNamespace

import pytest

from app import services
from app.agent_tools import AgentAnswer, run_summary_tool, summary_for_tool
from app.config import Settings


def summary():
    result = services.build_summary([{"date": "2026-01-01", "value": 2}], [])
    result["planning"] = {"count": 1, "scheduled_hours": 3, "sessions": [{"institution": "private place"}], "sessions_truncated": False}
    return result


def stub_client(monkeypatch, responses):
    requests = []
    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.responses = self
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return None
        def create(self, **kwargs):
            requests.append(kwargs)
            return responses[len(requests)-1]
    monkeypatch.setattr(services, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(services, "get_settings", lambda: Settings(openai_key="test-only"))
    return requests


def response(*, calls=(), text="", status="completed"):
    return SimpleNamespace(output=list(calls), output_text=text, status=status)


def call(name="get_data_summary", arguments="{}"):
    return SimpleNamespace(type="function_call", name=name, arguments=arguments, call_id="test-call")


def test_real_tool_flow_returns_result_to_model_and_caps_model_calls(monkeypatch):
    requests = stub_client(monkeypatch, [response(calls=[call()]), response(text="기록 1건, 교육시간 2시간입니다.")])
    answer = services.generate_answer(summary(), [{"role": "user", "content": "최신 수치를 확인해 줘"}])
    assert answer == "기록 1건, 교육시간 2시간입니다."
    assert answer.tool_calls[0]["name"] == "get_data_summary"
    assert len(requests) == 2 and requests[1]["tool_choice"] == "none"
    output = requests[1]["input"][-1]
    assert output["type"] == "function_call_output" and '"total": 2' in output["output"]
    assert "private place" not in output["output"]
    assert requests[0]["store"] is False and requests[1]["store"] is False


def test_direct_answer_does_not_force_an_unnecessary_second_call(monkeypatch):
    requests = stub_client(monkeypatch, [response(text="기록을 읽는 기준입니다.")])
    answer = services.generate_answer(summary(), [{"role": "user", "content": "연인원이 뭔가요?"}])
    assert isinstance(answer, AgentAnswer) and answer.tool_calls == [] and len(requests) == 1


@pytest.mark.parametrize("item", [call(name="delete_data"), call(arguments='{"id":"other"}'), call(arguments="not json")])
def test_unapproved_tool_or_arguments_never_execute(monkeypatch, item):
    requests = stub_client(monkeypatch, [response(calls=[item])])
    with pytest.raises(services.ChatUnavailable):
        services.generate_answer(summary(), [{"role": "user", "content": "확인"}])
    assert len(requests) == 1


def test_incomplete_tool_response_is_rejected_without_second_request(monkeypatch):
    requests = stub_client(monkeypatch, [response(calls=[call()], status="incomplete")])
    with pytest.raises(services.ChatUnavailable):
        services.generate_answer(summary(), [{"role": "user", "content": "확인"}])
    assert len(requests) == 1


def test_summary_tool_preserves_aggregate_and_excludes_schedule_details():
    result = run_summary_tool("get_data_summary", {}, summary())
    assert result["metrics"]["total"] == 2
    assert result["planning"] == {"count": 1, "scheduled_hours": 3}
    assert result == summary_for_tool(summary())


def test_trend_measures_hours_when_record_count_moves_in_opposite_direction():
    result = services.build_summary([
        {"date": "2026-09-01", "value": 1}, {"date": "2026-09-02", "value": 1},
        {"date": "2026-10-01", "value": 3},
    ], [])
    assert result["trend"]["metric"] == "education_hours"
    assert result["trend"]["percent"] == 50
