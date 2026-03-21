# Gemini Web API Reverse Engineering Walkthrough

> **Last Updated:** 2026-01-21
> **Capture Session:** `captures/projects/Gemini Web/gemini.google.com/session-20260121-163014/`

---

## Table of Contents

1. [Overview](#overview)
2. [API Architecture](#api-architecture)
3. [Core Streaming Endpoint](#core-streaming-endpoint)
4. [Authentication Flow](#authentication-flow)
5. [How to Find and Update Model Codes](#how-to-find-and-update-model-codes)
6. [How to Extract Cookies](#how-to-extract-cookies)
7. [Request Payload Structure](#request-payload-structure)
8. [Response Format](#response-format)
9. [Important Headers](#important-headers)
10. [Future Updates Guide](#future-updates-guide)
11. [Common Issues and Solutions](#common-issues-and-solutions)

---

## Overview

The Gemini Web API is Google's web interface for their AI models (Gemini 2.0 Flash, Pro, Ultra, etc.). Unlike the official Gemini API, the web API:

- Uses **cookie-based session authentication** (not API keys)
- Streams responses via **chunked HTTP responses** (not SSE)
- Uses a **form-encoded request body** with nested JSON data
- Requires specific **Google-specific headers**

### Key Domains

| Domain | Purpose |
|--------|---------|
| `gemini.google.com` | Main API endpoint |
| `accounts.google.com` | Cookie rotation and authentication |
| `play.google.com` | Analytics logging (can be ignored) |

---

## API Architecture

```
┌─────────────────────┐
│   Web Browser       │
│   (Cookie-based)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│  POST /u/{user_id}/_/BardChatUi/data/                           │
│       assistant.lamda.BardFrontendService/StreamGenerate        │
│                                                                  │
│  Query Params:                                                   │
│    - bl: Server build version (e.g., boq_assistant-bard-web-*) │
│    - f.sid: Session ID (changes per page load)                  │
│    - hl: Language code (e.g., "en")                             │
│    - _reqid: Request counter (increments per request)           │
│    - rt: Response type ("c" for chunked)                        │
└─────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────┐
│  Chunked Response   │
│  (JSON arrays)      │
└─────────────────────┘
```

---

## Core Streaming Endpoint

### Endpoint URL Pattern

```
POST https://gemini.google.com/u/{user_index}/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate
```

### URL Components

| Component | Description | Example |
|-----------|-------------|---------|
| `{user_index}` | Google account index (0, 1, 2...) | `1` |
| `bl` | Build/version identifier | `boq_assistant-bard-web-server_20260119.07_p1` |
| `f.sid` | Frontend session ID | `1117849236129373831` |
| `hl` | Language | `en` |
| `_reqid` | Request ID (incrementing) | `3359431` |
| `rt` | Response type | `c` (chunked) |

### Example Full URL

```
https://gemini.google.com/u/1/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate?bl=boq_assistant-bard-web-server_20260119.07_p1&f.sid=1117849236129373831&hl=en&_reqid=3359431&rt=c
```

---

## Authentication Flow

### Cookie-Based Authentication

The Gemini Web API uses Google's session cookies for authentication. **No API key is needed.**

### Critical Cookies (Must-Have)

| Cookie Name | Domain | Purpose | Lifespan |
|-------------|--------|---------|----------|
| `__Secure-1PSID` | `.google.com` | Primary session ID | ~1 year |
| `__Secure-3PSID` | `.google.com` | Third-party session ID | ~1 year |
| `SAPISID` | `.google.com` | API session ID | ~1 year |
| `__Secure-1PAPISID` | `.google.com` | Secure API session | ~1 year |
| `SIDCC` | `.google.com` | Session verification | ~1 year |
| `__Secure-1PSIDCC` | `.google.com` | Secure session verification | ~1 year |
| `__Secure-3PSIDCC` | `.google.com` | Third-party verification | ~1 year |
| `COMPASS` | `gemini.google.com` | Gemini-specific preferences | ~10 days |

### Secondary Cookies (Recommended)

| Cookie Name | Purpose |
|-------------|---------|
| `HSID` | HTTP session ID |
| `SSID` | Secure session ID |
| `SID` | General session ID |
| `NID` | NID preference cookie |
| `__Secure-1PSIDTS` | Timestamp-based session |
| `__Secure-3PSIDTS` | Timestamp-based session (3rd party) |

---

## How to Find and Update Model Codes

### Where Model Codes Appear

Model codes are embedded in the **request body** (form data), NOT in the URL. They are part of a nested JSON structure.

### Step-by-Step: Finding Model Code

1. **Open Chrome DevTools** (F12)
2. **Go to Network tab**
3. **Start a chat in Gemini**
4. **Find the `StreamGenerate` request**
5. **Look at Form Data / Payload**

### Model Code Location in Request Body

The request body is URL-encoded form data containing a field called `f.req`. Inside `f.req` is a JSON array structure:

```
f.req=[[[prompt_text,0,null,null,[0],null,null,null,0,null,null,null,0,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,0,null,null,null,null,null,null,null,null,null,[model_code]...]]]
```

### Known Model Codes (As of Jan 2026)

| Model | Model Code Pattern |
|-------|-------------------|
| Gemini 2.0 Flash | `gemini-2.0-flash-exp` |
| Gemini 2.0 Flash Thinking | `gemini-2.0-flash-thinking-exp` |
| Gemini 1.5 Pro | `gemini-1.5-pro` |
| Gemini 1.5 Flash | `gemini-1.5-flash` |
| Gemini Pro | `gemini-pro` |

### How to Discover New Model Codes

1. **Capture traffic** when switching models in the UI
2. **Search for patterns** like `gemini-*` in request bodies
3. **Check the JavaScript** - search for model identifiers in the page source
4. **Monitor the `bl` parameter** - new versions may indicate new models

---

## How to Extract Cookies

### Method 1: Browser DevTools (Manual)

1. Go to `https://gemini.google.com`
2. Open DevTools (F12) → Application tab → Cookies
3. Copy all cookies from `.google.com` and `gemini.google.com`

### Method 2: Using EditThisCookie Extension

1. Install "EditThisCookie" Chrome extension
2. Navigate to Gemini
3. Click the extension icon
4. Export cookies as JSON

### Method 3: Using mitmproxy (Automated)

```bash
# Start mitmproxy
mitmproxy -p 8080

# Configure browser to use proxy
# Browse to gemini.google.com and login
# Cookies will be captured in the traffic
```

### Method 4: Python Script with Browser Automation

```python
from playwright.sync_api import sync_playwright

def extract_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Navigate and login manually
        page.goto("https://gemini.google.com")
        input("Press Enter after logging in...")

        # Extract cookies
        cookies = context.cookies()
        for cookie in cookies:
            if cookie['domain'] in ['.google.com', 'gemini.google.com']:
                print(f"{cookie['name']}: {cookie['value'][:50]}...")

        browser.close()
```

### Cookie String Format for Requests

```python
cookie_string = "; ".join([
    f"__Secure-1PSID={value1}",
    f"__Secure-3PSID={value2}",
    f"SAPISID={value3}",
    # ... other cookies
])
```

---

## Request Payload Structure

### Content-Type

```
Content-Type: application/x-www-form-urlencoded;charset=UTF-8
```

### Form Data Fields

| Field | Description |
|-------|-------------|
| `f.req` | Main request payload (nested JSON array) |
| `at` | Anti-CSRF token |

### f.req Structure (Simplified)

```json
[
  [
    [
      "prompt text here",
      0,
      null,
      null,
      [0],
      null,
      null,
      null,
      0,
      null,
      null,
      null,
      0,
      null,
      null,
      null,
      null,
      null,
      null,
      null,
      null,
      null,
      null,
      null,
      null,
      null,
      null,
      null,
      null,
      null,
      null,
      null,
      0,
      null,
      null,
      null,
      null,
      null,
      null,
      null,
      null,
      null,
      ["model-code-here"]
    ]
  ]
]
```

### Finding the Anti-CSRF Token (`at`)

1. Load the Gemini page
2. Search page source for `SNlM0e` or look for a token pattern
3. The token is embedded in the initial HTML response

---

## Response Format

### Chunked Response Structure

The response is **NOT SSE**. It's a series of JSON arrays separated by newlines:

```
)]}'

<length>
[[["wrb.fr","response_id","[[nested_json_content]]",null,null,null,"generic"]],null]
<length>
[[["wrb.fr","response_id","[[more_content]]",null,null,null,"generic"]],null]
...
```

### Parsing Response

```python
def parse_gemini_response(raw_response: bytes) -> list:
    """Parse chunked Gemini response."""
    text = raw_response.decode('utf-8')

    # Remove the )]}' prefix
    if text.startswith(")]}'"):
        text = text[4:]

    results = []
    lines = text.strip().split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip length indicators (numeric lines)
        if line.isdigit():
            i += 1
            continue

        # Try to parse as JSON
        if line.startswith('['):
            try:
                data = json.loads(line)
                results.append(data)
            except json.JSONDecodeError:
                pass

        i += 1

    return results
```

---

## Important Headers

### Required Headers

```http
Content-Type: application/x-www-form-urlencoded;charset=UTF-8
Origin: https://gemini.google.com
Referer: https://gemini.google.com/
X-Same-Domain: 1
```

### Chrome-Specific Headers (Recommended)

```http
sec-ch-ua: "Chromium";v="143", "Not A(Brand";v="24", "Google Chrome";v="143"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "Windows"
sec-ch-ua-arch: "x86"
sec-ch-ua-bitness: "64"
sec-ch-ua-full-version-list: "Chromium";v="143.0.7499.193", ...
```

### Google Extension Headers

```http
X-Goog-Ext-73010989-Jspb: [0]
X-Goog-Ext-525001261-Jspb: [1,null,null,null,"session_id",null,null,0,[4],null,null,3]
X-Goog-Ext-525005358-Jspb: ["UUID",1]
```

---

## Future Updates Guide

### When Things Stop Working

1. **Check the `bl` parameter** - Google updates this regularly
   - Current: `boq_assistant-bard-web-server_20260119.07_p1`
   - Format: `boq_assistant-bard-web-server_YYYYMMDD.XX_pX`

2. **Capture new traffic** to find the updated value

### Monitoring for Changes

```bash
# Re-run capture when API breaks
python .claude/skills/reverse-web-api/scripts/analyze-captures.py \
    "captures/projects/Gemini Web/session-NEW/requests.jsonl" \
    -o "captures/projects/Gemini Web/reverse-web-api-skill-result"
```

### Version Update Checklist

1. [ ] Capture new traffic with mitmproxy/Fiddler
2. [ ] Find updated `bl` parameter
3. [ ] Check for new cookies or headers
4. [ ] Verify model codes still work
5. [ ] Update SDK/client code

### Finding the Build Version (`bl`)

1. **From Network Traffic:**
   ```bash
   grep "bl=" captures/projects/Gemini\ Web/gemini.google.com/session-*/requests.jsonl
   ```

2. **From Page Source:**
   - Search for `boq_assistant-bard-web-server` in page HTML

---

## Common Issues and Solutions

### Issue: 401 Unauthorized

**Cause:** Cookies expired or missing critical cookies

**Solution:**
1. Re-login to Gemini in browser
2. Re-extract all cookies
3. Ensure `__Secure-1PSID` and `SAPISID` are included

### Issue: 403 Forbidden

**Cause:** Missing headers or CSRF token mismatch

**Solution:**
1. Include `X-Same-Domain: 1` header
2. Get fresh `at` token from page source
3. Include all `sec-ch-ua-*` headers

### Issue: Empty/Invalid Response

**Cause:** Outdated `bl` parameter or malformed request

**Solution:**
1. Capture fresh traffic to get new `bl` value
2. Verify `f.req` structure matches current format
3. Check `_reqid` is incrementing properly

### Issue: Rate Limited

**Cause:** Too many requests in short time

**Solution:**
1. Add delays between requests (2-5 seconds)
2. Rotate between different Google accounts
3. Use different session IDs

---

## Quick Reference

### Minimal Request Example

```python
import httpx

cookies = {
    "__Secure-1PSID": "YOUR_VALUE",
    "__Secure-3PSID": "YOUR_VALUE",
    "SAPISID": "YOUR_VALUE",
    # ... other required cookies
}

headers = {
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    "Origin": "https://gemini.google.com",
    "X-Same-Domain": "1",
}

# Construct f.req with prompt and model
f_req = json.dumps([[["Hello, how are you?", 0, None, None, [0]]]])

data = {
    "f.req": f_req,
    "at": "YOUR_CSRF_TOKEN",
}

response = httpx.post(
    "https://gemini.google.com/u/0/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate",
    params={
        "bl": "boq_assistant-bard-web-server_20260119.07_p1",
        "f.sid": "1234567890",
        "hl": "en",
        "_reqid": "100000",
        "rt": "c",
    },
    cookies=cookies,
    headers=headers,
    data=data,
)
```

---

## File Locations

| Purpose | Location |
|---------|----------|
| Raw captures | `captures/projects/Gemini Web/gemini.google.com/session-*/requests.jsonl` |
| Analysis report | `captures/projects/Gemini Web/reverse-web-api-skill-result/analysis-report.json` |
| Generated SDK | `captures/projects/Gemini Web/gemini.google.com/sdk/client.py` |
| This walkthrough | `docs/gemini-web-api-reverse-engineering-walkthrough.md` |

---

## Appendix: Cookie Export Script

```python
"""
Export Gemini cookies from browser to JSON file.
Usage: python export_cookies.py
"""

import json
import browser_cookie3

def export_gemini_cookies():
    # Get cookies from Chrome
    cj = browser_cookie3.chrome(domain_name='.google.com')

    cookies = {}
    for cookie in cj:
        if cookie.domain in ['.google.com', 'gemini.google.com']:
            cookies[cookie.name] = cookie.value

    with open('gemini_cookies.json', 'w') as f:
        json.dump(cookies, f, indent=2)

    print(f"Exported {len(cookies)} cookies to gemini_cookies.json")

if __name__ == "__main__":
    export_gemini_cookies()
```

---

## Appendix: Traffic Capture Setup

### Using mitmproxy

```bash
# Install
pip install mitmproxy

# Start proxy
mitmproxy -p 8080 --set block_global=false

# Configure browser proxy settings to use localhost:8080
# Browse Gemini and interact
# Export flows: File → Export → Flows as JSON
```

### Using Fiddler

1. Download Fiddler Classic
2. Enable HTTPS decryption (Tools → Options → HTTPS)
3. Capture traffic from Gemini
4. Export as HAR or Fiddler SAZ

---

*Document generated by reverse-web-api skill. Keep this document updated when Google changes the API.*
