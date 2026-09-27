#!/usr/bin/env bash
# Opens kader with drawn demo rolls of the shrippen demo world (internal, for screenshots).
#   demo/start.sh [FOLDER] [kader open options, e.g. --no-browser --port 8123]
# FOLDER defaults to KADER_CACHE/demo-rollen (a fresh temp dir when KADER_CACHE is unset).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${ROOT}/.venv/bin/python"
folder=""
if [[ $# -gt 0 && "$1" != -* ]]; then folder="$1"; shift; fi
export KADER_CACHE="${KADER_CACHE:-$(mktemp -d "${TMPDIR:-/tmp}/kader-demo-XXXXXX")}"
folder="${folder:-${KADER_CACHE}/demo-rollen}"
echo "Demo: $("${PY}" "${ROOT}/demo/rolls.py" rolls "${folder}") drawn scans in ${folder}"
cd "${ROOT}"
exec "${PY}" -m companion open "${folder}" --new "$@"
