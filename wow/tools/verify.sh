#!/usr/bin/env bash
# Check every WoW export and prove the generated files are up to date. CI runs this;
# run it before committing any change under wow/.
#
# Usage: ./verify.sh
#        PYTHON=/path/to/python ./verify.sh
#
# Needs lupa (requirements.txt) and the pinned Lua sources (./fetch_deps.sh). Python is
# taken from $PYTHON, then ./.venv, then python3 on PATH.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$here"

py="${PYTHON:-}"
if [ -z "$py" ]; then
    if [ -x "$here/.venv/bin/python" ]; then py="$here/.venv/bin/python"; else py="python3"; fi
fi

out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT

step() { printf '\n== %s\n' "$*"; }

stale() {
    echo "FAIL: $1 is out of date. $2" >&2
    exit 1
}

step "Export checks"
"$py" check_exports.py

step "Decode both EllesmereUI profiles"
"$py" eui_decode.py ../ellesmereui/wow-forever.txt ../ellesmereui/retail.txt --out "$out"

step "Rebuild the retail profile from Forever"
"$py" eui_make_retail.py ../ellesmereui/wow-forever.txt "$out/rebuilt.txt"
cmp -s "$out/rebuilt.txt" ../ellesmereui/retail.txt ||
    stale wow/ellesmereui/retail.txt "Run: python3 eui_make_retail.py ../ellesmereui/wow-forever.txt ../ellesmereui/retail.txt"

step "Simulate the layout merge on each client"
"$py" eui_verify_layout.py ../ellesmereui/wow-forever.txt --client forever
"$py" eui_verify_layout.py ../ellesmereui/retail.txt --client retail

step "Convert the Edit Mode layout to retail"
"$py" editmode_convert.py ../blizz-ui/Craigtho-forever.txt "$out/em.txt"
cmp -s "$out/em.txt" ../blizz-ui/Craigtho-retail.txt ||
    stale wow/blizz-ui/Craigtho-retail.txt "Run: python3 editmode_convert.py ../blizz-ui/Craigtho-forever.txt ../blizz-ui/Craigtho-retail.txt"

printf '\nAll WoW checks passed.\n'
