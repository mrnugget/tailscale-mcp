# tailscale-mcp

Super small MCP server that allows Claude to query Tailscale status by running
the `tailscale` CLI on macOS.

VERY DRAFTY!

## Requirements

- Python
- Tailscale installed at `/Applications/Tailscale.app/Contents/MacOS/Tailscale`
- [uv](https://github.com/astral/uv) for dependency management

## Running the Server

### STDIO Transport (Default)

Run the server with stdio transport (default):
```bash
python tailscale.py
```

### HTTP/SSE Transport

Run the server with HTTP transport on a specific port:
```bash
python tailscale.py --transport http --port 4001
```
