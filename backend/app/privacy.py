"""Small, deterministic redaction at the model boundary; not full PII detection."""
import re

RULES = [
    (re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA )?PRIVATE KEY-----"), "[비공개 키 가림]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"), "[API 키 가림]"),
    (re.compile(r"(?<!\d)\d{6}\s*-\s*[1-8]\d{6}(?!\d)"), "[주민번호 형식 가림]"),
    (re.compile(r"(?<!\d)0(?:1[016789]|2|[3-6]\d)[- .]?\d{3,4}[- .]?\d{4}(?!\d)"), "[연락처 가림]"),
    (re.compile(r"(?<![A-Za-z0-9_.+-])[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,}(?![A-Za-z0-9_.-])"), "[이메일 가림]"),
]


def redact_text(text):
    for pattern, replacement in RULES:
        text = pattern.sub(replacement, text)
    return text


def redact_value(value):
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_value(item) for key, item in value.items()}
    return value
