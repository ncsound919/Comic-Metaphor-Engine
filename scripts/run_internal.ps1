# Run the Comic Metaphor Engine as an internal strategy/decision tool.
#   - FastAPI service on http://127.0.0.1:8000 (JSON API)
#   - MCP server on stdio (add to your agent's MCP config: `python mcp/server.py`)
param(
    [int]$Port = 8000,
    [switch]$Mcp
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
if ($Mcp) {
    Write-Host "Starting Comic Metaphor Engine MCP server (stdio)..."
    python mcp/server.py
} else {
    Write-Host "Starting Comic Metaphor Engine API on http://127.0.0.1:$Port ..."
    python -m uvicorn api.main:app --host 127.0.0.1 --port $Port
}
