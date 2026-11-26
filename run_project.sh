#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="${PYTHON_BIN:-python3}"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="${PYTHON_BIN:-python}"
else
  echo "Python is not installed or not available in PATH."
  echo "Install Python, then run this script again."
  exit 1
fi

export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-8000}"

LOCAL_URL="http://127.0.0.1:${PORT}"

echo "Smart AI Interview Coach"
echo "Project folder: $(pwd)"
echo "Python: ${PYTHON_BIN}"
echo "Requested URL: ${LOCAL_URL}"
echo

if command -v curl >/dev/null 2>&1; then
  if curl -fsS "${LOCAL_URL}/api/health" 2>/dev/null | grep -q '"Smart AI Interview Coach"' 2>/dev/null; then
    echo "The project is already running."
    echo "Open: ${LOCAL_URL}"
    exit 0
  fi
fi

echo "Starting backend and frontend..."
echo "Keep this terminal open. Press Ctrl+C to stop."
echo

"${PYTHON_BIN}" app.py &
APP_PID=$!
trap 'kill "$APP_PID" 2>/dev/null || true' EXIT INT TERM

for attempt in $(seq 1 30); do
  for candidate in $(seq "$PORT" $((PORT + 10))); do
    if curl -fsS "http://127.0.0.1:${candidate}/api/health" 2>/dev/null \
      | grep -q '"Smart AI Interview Coach"' 2>/dev/null; then
      echo "Open: http://127.0.0.1:${candidate}"
      break 2
    fi
  done
  if ! kill -0 "$APP_PID" 2>/dev/null; then
    wait "$APP_PID"
    exit $?
  fi
  sleep 0.2
done

wait "$APP_PID"
