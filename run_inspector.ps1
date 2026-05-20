Write-Host "🤖 Launching MCP Inspector Workspace..." -ForegroundColor Cyan
Start-Process "http://localhost:5173"

Write-Host "🚀 Connecting to Smart Room Digital Twin Engine..." -ForegroundColor Green
$env:MCP_IN_INSPECTOR="1"
npx @modelcontextprotocol/inspector venv/Scripts/python.exe digital_twin_server.py