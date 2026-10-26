from copy import deepcopy
import json
import pytest

from app.privacy import redact_text, redact_value
from test_agent_tools import stub_client, response, call, summary
from app import services


@pytest.mark.parametrize("sample", ["010-1234-5678", "0212345678", "demo@example.com", "900101-1234567", "sk-"+"testonly"*5])
def test_known_identifier_patterns_are_masked(sample):
    assert sample not in redact_text("연습용: "+sample)


@pytest.mark.parametrize("suffix", ["은", "입니다", "으로 문의"])
def test_korean_particles_do_not_prevent_email_redaction(suffix):
    assert redact_text("예시 이메일 demo@example.com"+suffix) == "예시 이메일 [이메일 가림]"+suffix


def test_recursive_masking_preserves_statistics_and_originals():
    original = {"period": "2026-10-26", "hours": 12.5, "count": 100, "notes": ["010-1234-5678"], "flag": False}
    before = deepcopy(original)
    safe = redact_value(original)
    assert original == before and safe["hours"] == 12.5 and safe["count"] == 100
    assert safe["period"] == "2026-10-26" and safe["flag"] is False
    assert safe["notes"] == ["[연락처 가림]"]


def test_identifiers_never_reach_either_model_request_or_tool_result(monkeypatch):
    requests = stub_client(monkeypatch, [response(calls=[call()]), response(text="확인했습니다")])
    context = summary()
    context["notes"] = ["연락처 demo@example.com"]
    before = deepcopy(context)
    services.generate_answer(context, [{"role": "user", "content": "010-1234-5678 통계 확인"}])
    assert context == before
    encoded = json.dumps(requests, ensure_ascii=False, default=str)
    assert "demo@example.com" not in encoded and "010-1234-5678" not in encoded
    assert len(requests) == 2
