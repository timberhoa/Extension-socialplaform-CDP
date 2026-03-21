# Request Capture Tool

A powerful HTTP/S traffic capture tool for API reverse engineering. Captures all browser requests via proxy, logs them in LLM-friendly formats for analysis.

## Features

- **Real-time streaming** - See requests as they happen
- **Multi-site support** - Organizes captures by domain
- **LLM-ready output** - JSON Lines + Markdown summary
- **Analysis hints** - Auto-detects auth patterns, API versions, tokens
- **HAR export** - Standard format for browser DevTools

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Capture

```bash
python run_capture.py
```

### 3. Configure Browser Proxy

Set your browser's HTTP/HTTPS proxy to `localhost:8080`

For Firefox:
- Settings → Network Settings → Manual proxy
- HTTP Proxy: localhost, Port: 8080
- Check "Also use this proxy for HTTPS"

### 4. Install CA Certificate (for HTTPS)

Visit http://mitm.it after configuring proxy and install the certificate for your OS/browser.

### 5. Browse Target Site

Navigate to the website you want to analyze. All requests will be captured.

### 6. Stop and Review

Press `Ctrl+C` to stop. Find captures in:

```
captures/
├── example.com/
│   └── session-20260121-160000/
│       ├── requests.jsonl    # Streaming JSON (for LLM)
│       ├── summary.md        # Human readable summary
│       └── traffic.har       # Standard HAR format
```

## CLI Options

```
python run_capture.py [options]

Options:
  --port, -p     Proxy port (default: 8080)
  --output, -o   Output directory (default: ./captures)
  --verbose, -v  Show headers and bodies in console
  --all, -a      Capture all requests including static assets
  --web          Use mitmproxy web UI instead of CLI
```

## Output Format

### requests.jsonl (LLM Analysis)

Each line is a complete JSON object:

```json
{
  "id": "req_000001",
  "timestamp": "2026-01-21T16:00:00.123Z",
  "method": "POST",
  "url": "https://api.example.com/v1/generate",
  "host": "api.example.com",
  "path": "/v1/generate",
  "query_params": {},
  "request": {
    "headers": {"authorization": "Bearer xxx..."},
    "cookies": {"session": "abc123"},
    "body": {"prompt": "Hello"},
    "content_type": "application/json"
  },
  "response": {
    "status_code": 200,
    "headers": {},
    "body": {"result": "..."},
    "timing_ms": 245
  },
  "analysis_hints": {
    "auth_type": "bearer",
    "api_version": "v1",
    "endpoint_type": "create",
    "auth_tokens": [...]
  }
}
```

### summary.md (Quick Reference)

Markdown summary with:
- Discovered endpoints
- Authentication tokens found
- Request patterns for replay

## Using with LLM

Feed the `requests.jsonl` file to Claude/GPT for analysis:

```
Analyze this API traffic capture. Identify:
1. Authentication flow and required tokens
2. API endpoint patterns
3. Required headers for each endpoint
4. Rate limiting behavior
5. Generate Python code to replay key requests
```

## Architecture

```
src/capture/
├── addon.py       # Main mitmproxy addon
├── analysis.py    # Auth/pattern detection
├── formatters.py  # JSON/Markdown/HAR output
└── console.py     # Real-time console display
```
