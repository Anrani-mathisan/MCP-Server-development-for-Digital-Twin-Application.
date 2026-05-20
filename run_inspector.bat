@echo off
echo 🤖 Launching MCP Inspector Workspace...
start http://localhost:5173

echo 🚀 Connecting to Smart Room Digital Twin Engine...
set MCP_IN_INSPECTOR=1
npx @modelcontextprotocol/inspector venv\Scripts\python.exe digital_twin_server.py
