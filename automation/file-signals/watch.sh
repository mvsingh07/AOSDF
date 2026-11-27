#!/bin/bash
# Explicit project inputs only. Notification does not authorize execution.
set -eu
here="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$here/file_watch.py" "$@"
