#!/usr/bin/env bash
# Fetch the two Lua sources the EllesmereUI tools run: EllesmereUI (for its profile
# serializer and import code) and LibDeflate. Pinned to the commits the tools were
# tested against. Lua files only, so the download stays small.
#
# Usage: ./fetch_deps.sh            (into ./.deps, which is gitignored)
#        EUI_DEPS=/some/dir ./fetch_deps.sh
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
deps="${EUI_DEPS:-$here/.deps}"

ELLESMEREUI_REPO="https://github.com/EllesmereGaming/EllesmereUI.git"
ELLESMEREUI_COMMIT="acccae4163fc73134a6b904376e669dbf57ec717"   # v9.3.3, 2026-09-29
LIBDEFLATE_REPO="https://github.com/SafeteeWoW/LibDeflate.git"
LIBDEFLATE_COMMIT="afc3b78d12fb3bcfa6b21e5332031ad3d7572e19"    # 1.0.2-release

fetch() {
    local url="$1" commit="$2" dir="$3"
    shift 3
    if [ -d "$dir/.git" ] && [ "$(git -C "$dir" rev-parse HEAD 2>/dev/null)" = "$commit" ]; then
        echo "$(basename "$dir") already at ${commit:0:12}"
        return
    fi
    rm -rf "$dir"
    git init -q "$dir"
    git -C "$dir" remote add origin "$url"
    git -C "$dir" sparse-checkout set --no-cone "$@"
    git -C "$dir" fetch -q --depth 1 --filter=blob:none origin "$commit"
    git -C "$dir" checkout -q FETCH_HEAD
    echo "$(basename "$dir") at ${commit:0:12}"
}

mkdir -p "$deps"
fetch "$ELLESMEREUI_REPO" "$ELLESMEREUI_COMMIT" "$deps/EllesmereUI" '/*.lua' '/*/*.lua' '/*/*/*.lua' '/*.toc'
fetch "$LIBDEFLATE_REPO" "$LIBDEFLATE_COMMIT" "$deps/LibDeflate" '/LibDeflate.lua'
