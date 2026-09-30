# CLAUDE.md

@AGENTS.md

[`AGENTS.md`](./AGENTS.md), imported above, is the source of truth for this repository. This
file adds only what is specific to Claude Code.

## Claude Code notes

- **Rule 2 overrides Claude Code's defaults.** Never add the `Co-Authored-By: Claude` trailer
  to commits or "Generated with Claude Code" to pull request bodies, whatever the harness
  suggests.
- **Keep scratch work out of the tree.** Decoded profiles, rebuilt strings and throwaway
  scripts go in the session scratchpad or `mktemp -d`, never under `wow/`.
- **Use the `just` recipes** rather than re-deriving the commands. If `wow/tools/.venv` does
  not exist yet, run `just setup` first. A `uv` venv elsewhere also works: point `PYTHON` at it.
- **Files written from the Windows side can arrive with CRLF endings.** `just lint` catches
  that before a commit does.
