#!/bin/bash
# Double-click to start DryOut Shield locally (macOS). Close this window or press Ctrl+C to stop.
set -e
cd "$(dirname "$0")"
PORT=8501

# Python environment: reuse the SCA folder's .venv, otherwise create one here (first run only)
if [ -x "../.venv/bin/python" ]; then
  PY="../.venv/bin/python"
elif [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  echo "First run: creating a Python environment and installing packages (2-3 minutes)..."
  python3 -m venv .venv
  PY=".venv/bin/python"
  "$PY" -m pip install --quiet --upgrade pip
fi
"$PY" -c "import streamlit, plotly, fpdf, statsmodels" 2>/dev/null || "$PY" -m pip install --quiet -r app/requirements.txt

if lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; then
  echo "DryOut Shield is already running at http://localhost:$PORT"
  open "http://localhost:$PORT"
  exit 0
fi

IP=$(ipconfig getifaddr en0 2>/dev/null || true)
echo ""
echo "  DryOut Shield is starting..."
echo "  On this Mac:            http://localhost:$PORT"
[ -n "$IP" ] && echo "  Same Wi-Fi (teammates): http://$IP:$PORT"
echo "  Stop: close this window or press Ctrl+C"
echo ""
(sleep 4 && open "http://localhost:$PORT") &
cd app
exec "../$PY" -m streamlit run streamlit_app.py --server.port $PORT --server.headless true
