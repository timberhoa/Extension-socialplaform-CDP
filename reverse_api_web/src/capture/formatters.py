"""
Output formatters - JSON Lines, Markdown summary, HAR export
Structures captured data for LLM analysis and standard tooling
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

# Use orjson if available for performance, fallback to json
try:
    import orjson
    def json_dumps(obj: Any) -> str:
        return orjson.dumps(obj, option=orjson.OPT_INDENT_2).decode()
    def json_dumps_compact(obj: Any) -> str:
        return orjson.dumps(obj).decode()
except ImportError:
    def json_dumps(obj: Any) -> str:
        return json.dumps(obj, indent=2, default=str)
    def json_dumps_compact(obj: Any) -> str:
        return json.dumps(obj, default=str)


class JsonLinesFormatter:
    """Writes requests as JSON Lines (one JSON object per line) for streaming"""

    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, record: dict[str, Any]) -> None:
        """Append a single record to the JSONL file"""
        with open(self.output_path, "a", encoding="utf-8") as f:
            f.write(json_dumps_compact(record) + "\n")


class MarkdownSummaryFormatter:
    """Generates human/LLM readable Markdown summary of captured traffic"""

    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.requests: list[dict] = []
        self.session_start = datetime.now()

    def add_request(self, record: dict[str, Any]) -> None:
        """Add a request record for summarization"""
        self.requests.append(record)

    def write_summary(self, domain: str) -> None:
        """Generate and write the Markdown summary"""
        content = self._generate_summary(domain)
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _generate_summary(self, domain: str) -> str:
        """Generate Markdown summary content"""
        lines = [
            f"# Traffic Capture Summary: {domain}",
            f"",
            f"**Session Start:** {self.session_start.isoformat()}",
            f"**Total Requests:** {len(self.requests)}",
            f"",
            "---",
            "",
            "## Endpoints Discovered",
            "",
        ]

        # Group by endpoint
        endpoints: dict[str, list[dict]] = {}
        for req in self.requests:
            key = f"{req['method']} {req['path']}"
            if key not in endpoints:
                endpoints[key] = []
            endpoints[key].append(req)

        for endpoint, reqs in sorted(endpoints.items()):
            lines.append(f"### {endpoint}")
            lines.append(f"- **Calls:** {len(reqs)}")

            # Show first request details
            first = reqs[0]
            if first.get("analysis_hints", {}).get("auth_type"):
                lines.append(f"- **Auth:** {first['analysis_hints']['auth_type']}")
            if first.get("analysis_hints", {}).get("endpoint_type"):
                lines.append(f"- **Type:** {first['analysis_hints']['endpoint_type']}")

            lines.append("")

        # Auth tokens section
        lines.extend([
            "---",
            "",
            "## Authentication Tokens Found",
            "",
        ])

        tokens_seen = set()
        for req in self.requests:
            for token in req.get("analysis_hints", {}).get("auth_tokens", []):
                token_key = f"{token['type']}:{token['name']}"
                if token_key not in tokens_seen:
                    tokens_seen.add(token_key)
                    lines.append(f"- **{token['name']}** ({token['type']})")
                    lines.append(f"  - Pattern: `{token['pattern']}`")
                    lines.append("")

        # API patterns
        lines.extend([
            "---",
            "",
            "## Request Patterns for Replay",
            "",
            "```python",
            "# Example replay code structure",
            "import requests",
            "",
            "session = requests.Session()",
            "# Set headers from captured tokens above",
            "```",
            "",
        ])

        return "\n".join(lines)


class HarFormatter:
    """Exports captured traffic to HAR format for browser DevTools import"""

    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.entries: list[dict] = []
        self.start_time = datetime.now()

    def add_entry(self, record: dict[str, Any]) -> None:
        """Add a request/response entry"""
        entry = {
            "startedDateTime": record.get("timestamp", datetime.now().isoformat()),
            "time": record.get("response", {}).get("timing_ms", 0),
            "request": {
                "method": record["method"],
                "url": record["url"],
                "httpVersion": "HTTP/1.1",
                "headers": [{"name": k, "value": v} for k, v in record.get("request", {}).get("headers", {}).items()],
                "queryString": [{"name": k, "value": v} for k, v in record.get("query_params", {}).items()],
                "cookies": [],
                "headersSize": -1,
                "bodySize": len(str(record.get("request", {}).get("body", ""))),
                "postData": {
                    "mimeType": record.get("request", {}).get("content_type", ""),
                    "text": json.dumps(record.get("request", {}).get("body", "")) if record.get("request", {}).get("body") else ""
                } if record["method"] in ["POST", "PUT", "PATCH"] else None
            },
            "response": {
                "status": record.get("response", {}).get("status_code", 0),
                "statusText": "",
                "httpVersion": "HTTP/1.1",
                "headers": [{"name": k, "value": v} for k, v in record.get("response", {}).get("headers", {}).items()],
                "cookies": [],
                "content": {
                    "size": len(str(record.get("response", {}).get("body", ""))),
                    "mimeType": record.get("response", {}).get("headers", {}).get("content-type", ""),
                    "text": json.dumps(record.get("response", {}).get("body", "")) if record.get("response", {}).get("body") else ""
                },
                "redirectURL": "",
                "headersSize": -1,
                "bodySize": -1
            },
            "cache": {},
            "timings": {
                "send": 0,
                "wait": record.get("response", {}).get("timing_ms", 0),
                "receive": 0
            }
        }
        self.entries.append(entry)

    def write(self) -> None:
        """Write HAR file"""
        har = {
            "log": {
                "version": "1.2",
                "creator": {
                    "name": "request-capture-tool",
                    "version": "1.0.0"
                },
                "entries": self.entries
            }
        }
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(json_dumps(har))
