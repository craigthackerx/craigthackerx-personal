# craigthackerx-personal

Craig's personal configuration. Today that means his World of Warcraft UI for WoW Forever
and retail, and the Python tools that build and check it.

[![CI](https://github.com/craigthackerx/craigthackerx-personal/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/craigthackerx/craigthackerx-personal/actions/workflows/ci.yml)
[![Licence](https://img.shields.io/github/license/craigthackerx/craigthackerx-personal)](./LICENSE)

---

## What is in here

| Path | What it is |
| --- | --- |
| [`wow/`](./wow) | The WoW UI: EllesmereUI profiles, Blizzard Edit Mode layouts and keybinds. [How to restore it](./wow/README.md). |
| [`wow/tools/`](./wow/tools) | Python tools that decode, generate and verify the UI strings. [Tool guide](./wow/tools/README.md). |
| [`.github/`](./.github) | CI workflow, the lint script, Dependabot and the pull request template. |
| [`justfile`](./justfile) | Entry points for everything: `just setup`, `just verify`, `just lint`. |
| [`AGENTS.md`](./AGENTS.md) | Rules and context for AI agents working here. [`CLAUDE.md`](./CLAUDE.md) points to it. |

Older material (Terraform, setup scripts, IDE settings, older addon exports) lives in the
[`legacy` tag](#legacy), not on `dev`.

## World of Warcraft UI

The UI is [EllesmereUI](https://github.com/EllesmereGaming/EllesmereUI), which replaced ElvUI,
plus a Blizzard Edit Mode layout and a keybinds file. WoW Forever is the source of truth: the
retail versions are generated from the Forever ones, so the two games share a layout and look.

```text
wow/ellesmereui/wow-forever.txt   --eui_make_retail.py-->   wow/ellesmereui/retail.txt
wow/blizz-ui/Craigtho-forever.txt --editmode_convert.py-->  wow/blizz-ui/Craigtho-retail.txt
wow/Bindings.wtf                  (shared by both games)
```

- To put the UI on a machine, follow [`wow/README.md`](./wow/README.md).
- To change it, change it in game on Forever, export, regenerate and verify. The same guide
  covers this.
- The profile and layout strings are opaque data. Never edit them by hand.

## Working on the repository

You need Python 3.10 or newer, git and bash. [`just`](https://github.com/casey/just) is
optional but saves typing.

```bash
just setup    # wow/tools/.venv with lupa, plus the pinned EllesmereUI and LibDeflate sources
just verify   # check every export and prove the generated files are up to date
just lint     # ruff, shellcheck, LF line endings, executable bits, dashes, secret material
just regen    # rebuild the retail files after changing a Forever one, then verify
```

Without `just`, the same commands are `wow/tools/verify.sh` and `.github/scripts/lint.sh`.
See [`wow/tools/README.md`](./wow/tools/README.md) for the manual setup.

## CI

[`.github/workflows/ci.yml`](./.github/workflows/ci.yml) runs on every push to `dev` and on
pull requests.

| Job | What it checks |
| --- | --- |
| WoW exports and tools | `wow/tools/verify.sh`: strings are well formed profile exports, both retail files regenerate byte for byte, and the layout merge simulates cleanly on each client. |
| Lint | `.github/scripts/lint.sh`: ruff, shellcheck, LF line endings, executable bits on scripts, no en or em dashes, no secret material. |
| Secret scan | gitleaks over the full git history. |

Actions are pinned to commit SHAs, the workflow token is read only, and gitleaks is fetched by
version and checksum. Dependabot proposes updates monthly.

## Legacy

Before the September 2026 tidy, this repository also held Terraform for DigitalOcean DNS and
its workflows, a TeamSpeak server stack, machine setup scripts for Windows and Fedora, IDE
settings, and the 2022 and 2025 addon exports (ElvUI, WeakAuras, VuhDo, Plater, Details,
OmniCD, DBM and BigWigs). All of it is kept in the `legacy` tag:

- Browse it: [`tree/legacy`](https://github.com/craigthackerx/craigthackerx-personal/tree/legacy)
- Restore a file: `git checkout legacy -- wow/elvui/0-elvui-pofile-import.txt`
- Developer environment setup now lives in
  [libre-devops/developer-environment](https://github.com/libre-devops/developer-environment).

## Licence

[MIT](./LICENSE).
