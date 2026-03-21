#!/bin/bash
# Start Request Capture Tool (Linux/macOS)
# Usage: ./start_capture.sh [options]

cd "$(dirname "$0")"

if [ ! -f ".venv/bin/python" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "Installing dependencies..."
    .venv/bin/pip install -r requirements.txt
fi

echo ""
echo "============================================================"
echo "  REQUEST CAPTURE TOOL"
echo "============================================================"
echo ""
echo "  Starting proxy on localhost:8080"
echo "  Configure your browser proxy to localhost:8080"
echo "  For HTTPS: visit http://mitm.it to install CA cert"
echo ""
echo "  Press Ctrl+C to stop and save capture"
echo ""
echo "============================================================"
echo ""

.venv/bin/mitmdump -s src/capture/addon.py --ssl-insecure "$@"
