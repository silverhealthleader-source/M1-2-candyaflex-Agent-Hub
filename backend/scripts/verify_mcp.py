"""Verify the adapter with a separate MCP client/server process, without printing records or keys."""
import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp import Client, StdioServerParameters

backend = Path(__file__).resolve().parents[1]
load_dotenv(backend / ".env")


async def main():
    parameters = StdioServerParameters(command=sys.executable, args=[str(backend / "mcp_server.py")],
                                      env={key: os.environ[key] for key in ["API_BASE_URL", "APP_ACCESS_TOKEN"] if key in os.environ})
    async with Client(parameters) as client:
        listed = await client.list_tools()
        assert [tool.name for tool in listed.tools] == ["get_data_summary"]
        result = await client.call_tool("get_data_summary", {})
        assert not result.is_error, "MCP 조회 실패: API 주소와 개인 키 설정을 확인해 주세요."
        payload = result.structured_content
        assert isinstance(payload, dict) and "metrics" in payload and "count" in payload
        report = {"passed": True, "transport": "stdio", "separate_server_process": True,
                  "tools": [tool.name for tool in listed.tools], "summary_schema_verified": True,
                  "protocol_version": client.protocol_version}
    destination = backend.parent / ".local/verification/mcp-client.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True))


if __name__ == "__main__":
    asyncio.run(main())
