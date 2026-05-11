#!/usr/bin/env python3
"""Smoke test for the Duplicati MCP server (Streamable HTTP transport)."""
import asyncio
import json
import sys

import httpx


def _parse_response(response: httpx.Response) -> dict:
    """Parse MCP response — handles both direct JSON and SSE event-stream."""
    content_type = response.headers.get("content-type", "")
    if "text/event-stream" in content_type:
        for line in response.text.splitlines():
            if line.startswith("data:"):
                payload = line[5:].strip()
                if payload and payload != "[DONE]":
                    return json.loads(payload)
        return {}
    return response.json() if response.content else {}


async def main(server_url: str = "http://localhost:3000") -> None:
    mcp_url = f"{server_url}/mcp"

    print(f"1️⃣  Sending initialize to {mcp_url}...")
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            init_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"},
                },
            }
            response = await client.post(
                mcp_url,
                json=init_msg,
                headers={"Accept": "application/json, text/event-stream"},
            )
            print(f"   HTTP status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', '?')}")

            if response.status_code == 200:
                print("✅ Initialize succeeded")
                session_id = response.headers.get("mcp-session-id")
                if session_id:
                    print(f"   Session ID: {session_id[:16]}...")
                data = _parse_response(response)
                server_info = data.get("result", {}).get("serverInfo", {})
                if server_info:
                    print(f"   Server: {server_info.get('name', '?')} v{server_info.get('version', '?')}")
            else:
                print(f"❌ Unexpected status: {response.status_code}")
                print(f"   Body: {response.text[:200]}")
                return

        except httpx.ConnectError as e:
            print(f"❌ Cannot connect to {mcp_url}: {e}")
            return

        session_headers = {"Accept": "application/json, text/event-stream"}
        if session_id:
            session_headers["mcp-session-id"] = session_id

        print(f"\n2️⃣  Listing tools...")
        try:
            tools_msg = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            }
            response = await client.post(
                mcp_url,
                json=tools_msg,
                headers=session_headers,
            )
            if response.status_code == 200:
                data = _parse_response(response)
                tools = data.get("result", {}).get("tools", [])
                print(f"✅ {len(tools)} tools available:")
                for tool in tools:
                    print(f"   - {tool['name']}")
            else:
                print(f"❌ tools/list failed: HTTP {response.status_code}")

        except Exception as e:
            print(f"❌ Error listing tools: {e}")


if __name__ == "__main__":
    server_param = sys.argv[1] if len(sys.argv) > 1 else "localhost:3000"
    if "://" not in server_param:
        server_param = f"http://{server_param}"
    print(f"Testing Duplicati MCP server at {server_param}\n")
    asyncio.run(main(server_param))
