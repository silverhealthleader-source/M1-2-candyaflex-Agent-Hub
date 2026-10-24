"""Optional stdio MCP adapter. It exposes one authenticated, read-only API tool."""
import os
from typing import Any
from urllib.parse import urlsplit

import httpx
from dotenv import load_dotenv
from mcp.server import MCPServer

from app.agent_tools import summary_for_tool
from app.config import BACKEND_DIR

load_dotenv(BACKEND_DIR / ".env")
mcp = MCPServer("CandyAflex education summary", instructions="교육기록을 조회하는 읽기 전용 도구입니다. 계획은 실적과 구분하세요.")


@mcp.tool(title="교육기록 요약 조회")
def get_data_summary() -> dict[str, Any]:
    """현재 연결한 강사 API의 전체 기간 교육기록 요약을 조회합니다. 수정·삭제하지 않습니다."""
    base = os.getenv("API_BASE_URL", "http://127.0.0.1:8010").rstrip("/")
    parsed = urlsplit(base)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("API_BASE_URL에는 인증정보·쿼리·앵커를 넣을 수 없습니다.")
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}):
        raise ValueError("로컬 주소 외에는 HTTPS API를 사용해 주세요.")
    token = os.getenv("APP_ACCESS_TOKEN", "")
    if parsed.hostname not in {"127.0.0.1", "localhost"} and not token:
        raise ValueError("원격 API의 개인 접속 키를 환경변수로 설정해 주세요.")
    try:
        with httpx.Client(timeout=75, follow_redirects=False) as client:
            response = client.get(base + "/api/data/summary", headers={"Authorization": "Bearer " + token} if token else {})
            response.raise_for_status()
            return summary_for_tool(response.json())
    except (httpx.HTTPError, ValueError) as exc:
        raise RuntimeError("교육 API에 연결하지 못했습니다. 주소·접속 키·서버 상태를 확인해 주세요.") from None


if __name__ == "__main__":
    mcp.run(transport="stdio")
