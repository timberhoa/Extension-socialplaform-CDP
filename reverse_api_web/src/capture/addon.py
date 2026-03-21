"""
Main mitmproxy addon - orchestrates capture, analysis, and output
This is the entry point loaded by mitmdump
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, parse_qs

# Add src directory to path for mitmproxy script loading
_script_dir = Path(__file__).parent
_src_dir = _script_dir.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from mitmproxy import http, ctx

from capture.analysis import extract_analysis_hints
from capture.formatters import JsonLinesFormatter, MarkdownSummaryFormatter, HarFormatter
from capture.console import ConsoleOutput


class RequestCaptureAddon:
    """
    mitmproxy addon that captures all HTTP/S traffic and logs it
    for LLM analysis and API reverse engineering
    """

    def __init__(self):
        self.output_base = Path("./captures")
        self.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.domain_formatters: dict[str, dict] = {}
        self.console = ConsoleOutput(verbose=False)
        self.request_count = 0

        # Domains to ignore (static assets, analytics, etc.)
        self.ignore_domains = {
            "fonts.googleapis.com",
            "fonts.gstatic.com",
            "www.google-analytics.com",
            "www.googletagmanager.com",
            "cdn.jsdelivr.net",
            "cdnjs.cloudflare.com",
        }

        # File extensions to ignore
        self.ignore_extensions = {
            ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg",
            ".ico", ".woff", ".woff2", ".ttf", ".eot", ".map"
        }

    def load(self, loader):
        """Called when addon is loaded"""
        loader.add_option(
            name="capture_output",
            typespec=str,
            default="./captures",
            help="Output directory for captured traffic"
        )
        loader.add_option(
            name="capture_verbose",
            typespec=bool,
            default=False,
            help="Enable verbose output with headers and bodies"
        )
        loader.add_option(
            name="capture_all",
            typespec=bool,
            default=False,
            help="Capture all requests including static assets"
        )

    def configure(self, updated):
        """Called when options are updated"""
        if "capture_output" in updated:
            self.output_base = Path(ctx.options.capture_output)
        if "capture_verbose" in updated:
            self.console = ConsoleOutput(verbose=ctx.options.capture_verbose)

        self.console.print_startup(8080, str(self.output_base))

    def response(self, flow: http.HTTPFlow) -> None:
        """Called when a response is received"""
        # Skip ignored domains/extensions unless capture_all is set
        if not getattr(ctx.options, 'capture_all', False):
            if self._should_ignore(flow):
                return

        # Build the record
        record = self._build_record(flow)

        # Get/create formatters for this domain
        formatters = self._get_formatters(flow.request.host)

        # Write to all outputs
        formatters["jsonl"].write(record)
        formatters["markdown"].add_request(record)
        formatters["har"].add_entry(record)

        # Console output
        self.console.print_request(record)
        self.request_count += 1

    def done(self):
        """Called when mitmproxy is shutting down"""
        # Write final summaries
        for domain, formatters in self.domain_formatters.items():
            formatters["markdown"].write_summary(domain)
            formatters["har"].write()

        self.console.print_shutdown(
            self.request_count,
            str(self.output_base)
        )

    def _should_ignore(self, flow: http.HTTPFlow) -> bool:
        """Check if request should be ignored"""
        host = flow.request.host
        path = flow.request.path.lower()

        # Check domain
        if host in self.ignore_domains:
            return True

        # Check extension
        for ext in self.ignore_extensions:
            if path.endswith(ext) or f"{ext}?" in path:
                return True

        return False

    def _get_formatters(self, domain: str) -> dict:
        """Get or create formatters for a domain.

        When output path is under captures/projects/, save all domains
        in a single session folder. Otherwise, group by domain.
        """
        # Check if using project-based structure
        output_str = str(self.output_base)
        is_project_mode = 'projects' in output_str

        if is_project_mode:
            # Project mode: single session folder for all domains
            cache_key = "__project__"
            if cache_key not in self.domain_formatters:
                session_dir = self.output_base / f"session-{self.session_id}"
                session_dir.mkdir(parents=True, exist_ok=True)

                self.domain_formatters[cache_key] = {
                    "jsonl": JsonLinesFormatter(session_dir / "requests.jsonl"),
                    "markdown": MarkdownSummaryFormatter(session_dir / "summary.md"),
                    "har": HarFormatter(session_dir / "traffic.har"),
                }
            return self.domain_formatters[cache_key]
        else:
            # Legacy mode: group by domain
            if domain not in self.domain_formatters:
                session_dir = self.output_base / domain / f"session-{self.session_id}"
                session_dir.mkdir(parents=True, exist_ok=True)

                self.domain_formatters[domain] = {
                    "jsonl": JsonLinesFormatter(session_dir / "requests.jsonl"),
                    "markdown": MarkdownSummaryFormatter(session_dir / "summary.md"),
                    "har": HarFormatter(session_dir / "traffic.har"),
                }
            return self.domain_formatters[domain]

    def _build_record(self, flow: http.HTTPFlow) -> dict[str, Any]:
        """Build a comprehensive record from flow"""
        request = flow.request
        response = flow.response

        # Parse URL
        parsed = urlparse(request.url)

        # Calculate timing
        timing_ms = 0
        if response and flow.response.timestamp_end and flow.request.timestamp_start:
            timing_ms = int((flow.response.timestamp_end - flow.request.timestamp_start) * 1000)

        record = {
            "id": f"req_{self.request_count + 1:06d}",
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "url": request.url,
            "host": request.host,
            "path": request.path,
            "query_params": dict(parse_qs(parsed.query)),

            "request": {
                "headers": dict(request.headers),
                "cookies": self._parse_cookies(request.headers.get("cookie", "")),
                "body": self._decode_body(request.content, request.headers.get("content-type", "")),
                "content_type": request.headers.get("content-type", ""),
            },

            "response": {
                "status_code": response.status_code if response else None,
                "headers": dict(response.headers) if response else {},
                "cookies_set": self._parse_set_cookies(response.headers.get_all("set-cookie") if response else []),
                "body": self._decode_body(
                    response.content if response else b"",
                    response.headers.get("content-type", "") if response else ""
                ),
                "timing_ms": timing_ms,
            },

            "analysis_hints": extract_analysis_hints(flow),
        }

        return record

    def _parse_cookies(self, cookie_header: str) -> dict[str, str]:
        """Parse Cookie header into dict"""
        cookies = {}
        if cookie_header:
            for cookie in cookie_header.split(";"):
                cookie = cookie.strip()
                if "=" in cookie:
                    name, value = cookie.split("=", 1)
                    cookies[name.strip()] = value.strip()
        return cookies

    def _parse_set_cookies(self, set_cookie_headers: list) -> list[dict]:
        """Parse Set-Cookie headers"""
        cookies = []
        for header in set_cookie_headers:
            parts = header.split(";")
            if parts:
                main = parts[0]
                if "=" in main:
                    name, value = main.split("=", 1)
                    cookies.append({
                        "name": name.strip(),
                        "value": value.strip()[:100] + "..." if len(value) > 100 else value.strip(),
                        "attributes": [p.strip() for p in parts[1:]]
                    })
        return cookies

    def _decode_body(self, content: bytes, content_type: str) -> Any:
        """Decode body based on content type"""
        if not content:
            return None

        content_type = content_type.lower()

        # Try JSON
        if "json" in content_type:
            try:
                return json.loads(content.decode("utf-8"))
            except:
                pass

        # Try text
        if any(t in content_type for t in ["text", "xml", "html", "javascript"]):
            try:
                text = content.decode("utf-8")
                # Truncate very long text
                if len(text) > 10000:
                    return text[:10000] + f"... [truncated, total {len(text)} chars]"
                return text
            except:
                pass

        # Binary - just return size info
        return f"[binary data: {len(content)} bytes]"


# Export addon instance for mitmproxy
addons = [RequestCaptureAddon()]
