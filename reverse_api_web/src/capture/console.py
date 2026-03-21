"""
Console output handler - real-time streaming with color coding
Uses Rich library for beautiful terminal output
"""

from datetime import datetime
from typing import Any

# Use Rich if available, fallback to basic print
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.table import Table
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ConsoleOutput:
    """Real-time console streaming with color coding"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.request_count = 0
        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None

    def print_request(self, record: dict[str, Any]) -> None:
        """Print a captured request to console"""
        self.request_count += 1

        if RICH_AVAILABLE:
            self._print_rich(record)
        else:
            self._print_basic(record)

    def _print_rich(self, record: dict[str, Any]) -> None:
        """Rich formatted output"""
        method = record["method"]
        status = record.get("response", {}).get("status_code", "---")

        # Color code by method
        method_colors = {
            "GET": "green",
            "POST": "yellow",
            "PUT": "blue",
            "PATCH": "cyan",
            "DELETE": "red",
            "OPTIONS": "dim",
            "HEAD": "dim",
        }
        method_color = method_colors.get(method, "white")

        # Color code by status
        if isinstance(status, int):
            if status < 300:
                status_color = "green"
            elif status < 400:
                status_color = "yellow"
            elif status < 500:
                status_color = "red"
            else:
                status_color = "bold red"
        else:
            status_color = "dim"

        # Build output line
        timing = record.get("response", {}).get("timing_ms", 0)
        endpoint_type = record.get("analysis_hints", {}).get("endpoint_type", "")
        auth_type = record.get("analysis_hints", {}).get("auth_type", "")

        # Main line
        self.console.print(
            f"[dim]#{self.request_count:04d}[/dim] "
            f"[{method_color}]{method:7}[/{method_color}] "
            f"[{status_color}]{status}[/{status_color}] "
            f"[dim]{timing:>5}ms[/dim] "
            f"{record['host']}{record['path'][:60]}"
        )

        # Tags line
        tags = []
        if auth_type:
            tags.append(f"[cyan]auth:{auth_type}[/cyan]")
        if endpoint_type:
            tags.append(f"[magenta]{endpoint_type}[/magenta]")

        if tags:
            self.console.print(f"         {' '.join(tags)}")

        # Verbose mode: show headers and body
        if self.verbose:
            self._print_verbose_details(record)

    def _print_verbose_details(self, record: dict[str, Any]) -> None:
        """Print detailed request/response in verbose mode"""
        if not RICH_AVAILABLE:
            return

        # Request headers
        req_headers = record.get("request", {}).get("headers", {})
        if req_headers:
            table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
            table.add_column("Header", style="cyan")
            table.add_column("Value", style="white")
            for k, v in list(req_headers.items())[:10]:  # Limit to 10 headers
                # Mask sensitive values partially
                display_val = v[:50] + "..." if len(v) > 50 else v
                table.add_row(k, display_val)
            self.console.print(table)

        # Request body
        req_body = record.get("request", {}).get("body")
        if req_body:
            try:
                import json
                body_str = json.dumps(req_body, indent=2)
                syntax = Syntax(body_str[:500], "json", theme="monokai", line_numbers=False)
                self.console.print(Panel(syntax, title="Request Body", border_style="dim"))
            except:
                self.console.print(f"[dim]Body: {str(req_body)[:200]}[/dim]")

        self.console.print("")

    def _print_basic(self, record: dict[str, Any]) -> None:
        """Basic print without Rich"""
        method = record["method"]
        status = record.get("response", {}).get("status_code", "---")
        timing = record.get("response", {}).get("timing_ms", 0)

        print(
            f"#{self.request_count:04d} {method:7} {status} {timing:>5}ms "
            f"{record['host']}{record['path'][:60]}"
        )

    def print_startup(self, port: int, output_dir: str) -> None:
        """Print startup banner"""
        if RICH_AVAILABLE:
            self.console.print(Panel(
                f"[bold green]Request Capture Tool[/bold green]\n\n"
                f"Proxy: [cyan]localhost:{port}[/cyan]\n"
                f"Output: [cyan]{output_dir}[/cyan]\n\n"
                f"Configure your browser to use this proxy.\n"
                f"Press Ctrl+C to stop and save summary.",
                title="Capture Started",
                border_style="green"
            ))
        else:
            print(f"\n=== Request Capture Tool ===")
            print(f"Proxy: localhost:{port}")
            print(f"Output: {output_dir}")
            print(f"Press Ctrl+C to stop\n")

    def print_shutdown(self, total_requests: int, output_dir: str) -> None:
        """Print shutdown summary"""
        if RICH_AVAILABLE:
            self.console.print(Panel(
                f"[bold]Capture Complete[/bold]\n\n"
                f"Total Requests: [cyan]{total_requests}[/cyan]\n"
                f"Output saved to: [cyan]{output_dir}[/cyan]",
                title="Done",
                border_style="green"
            ))
        else:
            print(f"\n=== Capture Complete ===")
            print(f"Total: {total_requests} requests")
            print(f"Saved to: {output_dir}\n")
