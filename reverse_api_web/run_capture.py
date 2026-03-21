#!/usr/bin/env python3
"""
Request Capture Tool - CLI Entry Point
Starts mitmproxy with the capture addon and project management.

Usage:
    python run_capture.py                    # Interactive project selection
    python run_capture.py --project MyAPI    # Use specific project
    python run_capture.py --port 8080        # Custom port

Then configure your browser to use localhost:8080 as HTTP/HTTPS proxy.
For HTTPS, install mitmproxy's CA certificate at http://mitm.it
"""

import argparse
import sys
import subprocess
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from capture.project_manager import (
    select_project_interactive,
    get_project_output_dir,
    list_projects,
    create_project
)


def main():
    parser = argparse.ArgumentParser(
        description="Capture HTTP/S traffic for API reverse engineering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Interactive project selection
    python run_capture.py

    # Use specific project
    python run_capture.py --project "Gemini Web"

    # Create and use new project
    python run_capture.py --project "New API" --new

    # Custom port with verbose output
    python run_capture.py --project MyAPI -p 9090 -v
        """
    )

    parser.add_argument(
        "--project", "-P",
        type=str,
        help="Project name to use (skips interactive selection)"
    )
    parser.add_argument(
        "--new", "-n",
        action="store_true",
        help="Create new project if --project specified and doesn't exist"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8080,
        help="Proxy port (default: 8080)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output with headers and bodies"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Capture all requests including static assets"
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Open mitmproxy web interface instead of CLI"
    )

    args = parser.parse_args()

    # Project selection
    if args.project:
        project_name = args.project
        existing = list_projects()
        if project_name not in existing:
            if args.new:
                create_project(project_name)
                print(f"Created new project: {project_name}")
            else:
                print(f"Error: Project '{project_name}' not found.")
                print(f"Use --new to create it, or choose from: {', '.join(existing)}")
                sys.exit(1)
    else:
        project_name = select_project_interactive()
        if not project_name:
            print("\nCapture cancelled.")
            sys.exit(0)

    output_dir = get_project_output_dir(project_name)

    # Get the addon script path
    addon_path = Path(__file__).parent / "src" / "capture" / "addon.py"
    if not addon_path.exists():
        addon_path = Path(__file__).parent / "capture" / "addon.py"

    if not addon_path.exists():
        print(f"Error: Cannot find addon.py at {addon_path}")
        sys.exit(1)

    # Resolve mitmdump/mitmweb path
    cmd_base = "mitmweb" if args.web else "mitmdump"
    cmd_exe = cmd_base + ".exe" if sys.platform == "win32" else cmd_base
    
    # Priority 1: Check .venv/Scripts (or .venv/bin on Unix)
    venv_dir = Path(__file__).parent / ".venv"
    venv_scripts = venv_dir / ("Scripts" if sys.platform == "win32" else "bin")
    venv_cmd = venv_scripts / cmd_exe
    
    # Priority 2: Check same directory as current python executable
    python_dir = Path(sys.executable).parent
    py_cmd = python_dir / cmd_exe
    
    if venv_cmd.exists():
        cmd_path = venv_cmd
    elif py_cmd.exists():
        cmd_path = py_cmd
    else:
        # Fallback to PATH
        cmd_path = cmd_base

    cmd = [
        str(cmd_path),
        "-s", str(addon_path),
        "-p", str(args.port),
        "--set", f"capture_output={output_dir}",
        "--set", f"capture_verbose={str(args.verbose).lower()}",
        "--set", f"capture_all={str(args.all).lower()}",
    ]

    print(f"\n{'='*60}")
    print("  REQUEST CAPTURE TOOL")
    print(f"{'='*60}")
    print(f"\n  Project: {project_name}")
    print(f"  Output:  {output_dir}")
    print(f"  Proxy:   localhost:{args.port}")
    print(f"  Mode:    {'Verbose' if args.verbose else 'Normal'}")
    print(f"\n  Configure your browser proxy to localhost:{args.port}")
    print(f"  For HTTPS: visit http://mitm.it to install CA cert")
    print(f"\n  Press Ctrl+C to stop and save capture")
    print(f"\n{'='*60}\n")

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\nCapture stopped.")
    except FileNotFoundError:
        print(f"\nError: '{cmd_base}' not found.")
        print("Please run using start_capture.bat (Windows) or start_capture.sh (Mac/Linux)")
        sys.exit(1)


if __name__ == "__main__":
    main()
