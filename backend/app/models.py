from datetime import date as Date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DataCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)
    date: Date
    value: float = Field(ge=0, le=24, description="해당 교육일의 교육시간")
    memo: str = Field(min_length=1, max_length=2000)
    course_title: str = Field(default="직접 등록 교육", min_length=1, max_length=200)
    mode: Literal["집합", "온라인", "에듀버스", "기타"] = "집합"
    venue: str = Field(default="", max_length=300)
    students: int = Field(default=0, ge=0, le=100000)


class DataUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)
    date: Date | None = None
    value: float | None = Field(default=None, ge=0, le=24)
    memo: str | None = Field(default=None, min_length=1, max_length=2000)
    course_title: str | None = Field(default=None, min_length=1, max_length=200)
    mode: Literal["집합", "온라인", "에듀버스", "기타"] | None = None
    venue: str | None = Field(default=None, max_length=300)
    students: int | None = Field(default=None, ge=0, le=100000)


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=12000)


class ConversationWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{1,100}$")
    title: str = Field(default="새 대화", min_length=1, max_length=100)
    messages: list[Message] = Field(min_length=1, max_length=100)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{1,100}$")
    date_from: Date | None = None
    date_to: Date | None = None
    agent_id: Literal["analysis", "report"] = "analysis"
