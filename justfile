# Task runner for this repository. Run `just` to list the recipes.
set shell := ["bash", "-euo", "pipefail", "-c"]

tools := "wow/tools"

# List the recipes
default:
    @just --list

# Create wow/tools/.venv with lupa, then fetch the pinned EllesmereUI and LibDeflate sources
setup:
    python3 -m venv {{tools}}/.venv
    {{tools}}/.venv/bin/pip install -q -r {{tools}}/requirements.txt
    {{tools}}/fetch_deps.sh

# Check every WoW export and prove the generated files are up to date
verify:
    {{tools}}/verify.sh

# Rebuild retail.txt and Craigtho-retail.txt from their Forever sources, then verify
regen:
    cd {{tools}} && "${PYTHON:-.venv/bin/python}" eui_make_retail.py ../ellesmereui/wow-forever.txt ../ellesmereui/retail.txt
    cd {{tools}} && "${PYTHON:-.venv/bin/python}" editmode_convert.py ../blizz-ui/Craigtho-forever.txt ../blizz-ui/Craigtho-retail.txt
    {{tools}}/verify.sh

# Lint Python, shell scripts, line endings, dashes and secret material
lint:
    .github/scripts/lint.sh

# Scan the full git history for secrets (needs gitleaks on PATH)
secrets:
    gitleaks git --no-banner --redact -v .

# Everything CI runs
ci: lint verify secrets
