#!/bin/bash

echo "=== Duplicati MCP Server Test ==="
echo

echo "1. Checking container..."
docker ps | grep duplicati-mcp-server
if [ $? -ne 0 ]; then
    echo "❌ Container is not running"
    exit 1
fi
echo "✅ Container active"
echo

echo "2. Testing MCP endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}')
if [ "$response" = "200" ]; then
    echo "✅ MCP endpoint responding (HTTP $response)"
else
    echo "❌ MCP endpoint returned HTTP $response"
fi
echo

echo "3. Checking logs..."
docker logs duplicati-mcp-server 2>&1 | tail -5
echo

echo "=== Test completed ==="
