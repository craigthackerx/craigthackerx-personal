#!/usr/bin/env bash
# Repository lint: Python (ruff), shell (shellcheck), line endings, executable bits,
# dashes in text, and secret material. CI runs this, and so does `just lint`.
#
# Usage: .github/scripts/lint.sh
#
# Checks tracked files plus untracked files that are not ignored, so it catches problems
# before they are committed. Needs ruff (or uv) and shellcheck on PATH.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

fail=0
problem() {
    # $1 = file, $2 = message. GitHub annotations in CI, plain text locally.
    if [ -n "${GITHUB_ACTIONS:-}" ]; then echo "::error file=$1::$2"; else echo "FAIL $1: $2"; fi
    fail=1
}
step() { printf '\n== %s\n' "$*"; }

mapfile -t files < <(git ls-files --cached --others --exclude-standard | sort -u)
mapfile -t scripts < <(printf '%s\n' "${files[@]}" | grep -E '\.sh$' || true)

step "ruff"
if command -v ruff >/dev/null; then ruff=(ruff); elif command -v uvx >/dev/null; then ruff=(uvx ruff); else
    echo "ruff not found: pip install -r wow/tools/requirements-dev.txt" >&2; exit 2
fi
(cd wow/tools && "${ruff[@]}" check .) || fail=1

step "shellcheck"
command -v shellcheck >/dev/null || { echo "shellcheck not found" >&2; exit 2; }
shellcheck -S warning "${scripts[@]}" || fail=1

# The repository is edited from Windows and run in WSL and CI. A CRLF shebang makes the
# interpreter unresolvable, and .gitattributes only normalises files once they are added.
step "Line endings and executable bits"
for f in "${files[@]}"; do
    [ -f "$f" ] || continue
    if grep -Iq $'\r' "$f"; then problem "$f" "CRLF line endings; this repository is LF only"; fi
done
while read -r mode _ _ f; do
    [ "$mode" = 100755 ] || problem "$f" "missing executable bit (git update-index --chmod=+x $f)"
done < <(git ls-files -s -- '*.sh')

# Matched as UTF-8 bytes so the result does not depend on the locale.
step "No en or em dashes"
if git grep -nI --untracked -e $'\xe2\x80\x93' -e $'\xe2\x80\x94'; then
    problem "." "en or em dashes found above: use commas, colons, brackets or separate sentences"
fi

# Belt and braces alongside .gitignore: catches a file force added past the ignore rules.
step "No secret material"
for f in "${files[@]}"; do
    case "$f" in
        *.key | *.pem | *.pfx | *.p12 | .env | .env.* | */.env | id_rsa | id_ed25519 | */id_rsa | */id_ed25519)
            problem "$f" "secret material must not be committed" ;;
    esac
done

if [ "$fail" -ne 0 ]; then
    printf '\nLint failed.\n' >&2
    exit 1
fi
printf '\nLint passed.\n'
