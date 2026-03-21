"""
Analysis hints extractor - detects auth patterns, API versions, tokens
Provides structured hints for LLM analysis
"""

import re
from typing import Any
from mitmproxy import http


def extract_analysis_hints(flow: http.HTTPFlow) -> dict[str, Any]:
    """Extract analysis hints from request/response for LLM consumption"""
    hints: dict[str, Any] = {}

    # Auth detection
    hints["auth_type"] = _detect_auth_type(flow)
    hints["auth_tokens"] = _extract_auth_tokens(flow)

    # API pattern detection
    hints["api_version"] = _detect_api_version(flow)
    hints["endpoint_type"] = _classify_endpoint(flow)

    # Rate limiting
    hints["rate_limit"] = _extract_rate_limit(flow)

    # Session info
    hints["session_indicators"] = _extract_session_indicators(flow)

    # Request patterns
    hints["request_pattern"] = _analyze_request_pattern(flow)

    return hints


def _detect_auth_type(flow: http.HTTPFlow) -> str | None:
    """Detect authentication type from headers"""
    req_headers = flow.request.headers

    auth_header = req_headers.get("authorization", "")
    if auth_header.lower().startswith("bearer"):
        return "bearer"
    if auth_header.lower().startswith("basic"):
        return "basic"
    if auth_header.lower().startswith("apikey"):
        return "api_key"

    # Check for API key in headers
    for header in req_headers:
        if "api" in header.lower() and "key" in header.lower():
            return "api_key_header"
        if "x-auth" in header.lower():
            return "custom_auth"

    # Check for session cookies
    if "cookie" in req_headers:
        cookies = req_headers.get("cookie", "")
        if any(s in cookies.lower() for s in ["session", "sid", "auth", "token"]):
            return "session_cookie"

    return None


def _extract_auth_tokens(flow: http.HTTPFlow) -> list[dict[str, str]]:
    """Extract authentication tokens for replay"""
    tokens = []
    req_headers = flow.request.headers

    # Authorization header
    if "authorization" in req_headers:
        tokens.append({
            "type": "header",
            "name": "Authorization",
            "value": req_headers["authorization"],
            "pattern": "Authorization: {value}"
        })

    # Custom auth headers
    for header, value in req_headers.items():
        if any(k in header.lower() for k in ["x-api", "x-auth", "x-token", "x-session"]):
            tokens.append({
                "type": "header",
                "name": header,
                "value": value,
                "pattern": f"{header}: {{value}}"
            })

    # Cookies with auth patterns
    if "cookie" in req_headers:
        for cookie in req_headers["cookie"].split(";"):
            cookie = cookie.strip()
            if "=" in cookie:
                name, value = cookie.split("=", 1)
                if any(k in name.lower() for k in ["session", "auth", "token", "sid", "jwt"]):
                    tokens.append({
                        "type": "cookie",
                        "name": name.strip(),
                        "value": value.strip(),
                        "pattern": f"Cookie: {name}={{value}}"
                    })

    return tokens


def _detect_api_version(flow: http.HTTPFlow) -> str | None:
    """Detect API version from path or headers"""
    path = flow.request.path

    # Path-based versioning: /v1/, /v2/, /api/v1/
    version_match = re.search(r"/v(\d+(?:\.\d+)?)/", path)
    if version_match:
        return f"v{version_match.group(1)}"

    # Header-based versioning
    for header in ["api-version", "x-api-version", "accept-version"]:
        if header in flow.request.headers:
            return flow.request.headers[header]

    return None


def _classify_endpoint(flow: http.HTTPFlow) -> str:
    """Classify endpoint type based on path and method"""
    path = flow.request.path.lower()
    method = flow.request.method

    # Common patterns
    if any(p in path for p in ["/auth", "/login", "/signin", "/oauth"]):
        return "authentication"
    if any(p in path for p in ["/register", "/signup"]):
        return "registration"
    if any(p in path for p in ["/logout", "/signout"]):
        return "logout"
    if any(p in path for p in ["/refresh", "/token"]):
        return "token_refresh"
    if any(p in path for p in ["/upload", "/file"]):
        return "file_operation"
    if any(p in path for p in ["/search", "/query"]):
        return "search"
    if any(p in path for p in ["/stream", "/sse", "/events"]):
        return "streaming"
    if any(p in path for p in ["/ws", "/websocket"]):
        return "websocket"
    if any(p in path for p in ["/graphql"]):
        return "graphql"

    # CRUD patterns
    if method == "GET" and not flow.request.query:
        return "read"
    if method == "GET" and flow.request.query:
        return "read_filtered"
    if method == "POST":
        return "create"
    if method in ["PUT", "PATCH"]:
        return "update"
    if method == "DELETE":
        return "delete"

    return "unknown"


def _extract_rate_limit(flow: http.HTTPFlow) -> dict[str, Any] | None:
    """Extract rate limiting information from response headers"""
    if not flow.response:
        return None

    rate_info = {}
    resp_headers = flow.response.headers

    for header, key in [
        ("x-ratelimit-limit", "limit"),
        ("x-ratelimit-remaining", "remaining"),
        ("x-ratelimit-reset", "reset"),
        ("retry-after", "retry_after"),
        ("x-rate-limit-limit", "limit"),
        ("x-rate-limit-remaining", "remaining"),
    ]:
        if header in resp_headers:
            rate_info[key] = resp_headers[header]

    return rate_info if rate_info else None


def _extract_session_indicators(flow: http.HTTPFlow) -> list[str]:
    """Extract session/state indicators"""
    indicators = []

    # Check Set-Cookie in response
    if flow.response and "set-cookie" in flow.response.headers:
        indicators.append("sets_cookies")

    # Check for CSRF tokens
    req_headers = flow.request.headers
    if any("csrf" in h.lower() for h in req_headers):
        indicators.append("uses_csrf")

    # Check for correlation IDs
    if any("correlation" in h.lower() or "request-id" in h.lower() for h in req_headers):
        indicators.append("has_correlation_id")

    # Check for idempotency keys
    if any("idempotency" in h.lower() for h in req_headers):
        indicators.append("uses_idempotency")

    return indicators


def _analyze_request_pattern(flow: http.HTTPFlow) -> dict[str, Any]:
    """Analyze request structure for pattern recognition"""
    pattern = {
        "has_query_params": bool(flow.request.query),
        "has_body": bool(flow.request.content),
        "content_type": flow.request.headers.get("content-type", "none"),
    }

    # Detect if body is JSON
    content_type = pattern["content_type"].lower()
    if "json" in content_type:
        pattern["body_format"] = "json"
    elif "form" in content_type:
        pattern["body_format"] = "form"
    elif "multipart" in content_type:
        pattern["body_format"] = "multipart"
    elif "xml" in content_type:
        pattern["body_format"] = "xml"
    else:
        pattern["body_format"] = "other"

    return pattern
