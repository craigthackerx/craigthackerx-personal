# WoW UI tools

Python tools that decode, generate and verify the UI strings in [`wow/`](../README.md).

The EllesmereUI tools do not reimplement anything. They run the addon's own serialiser, its
import code and the real LibDeflate in Lua 5.1 (through [lupa](https://github.com/scoder/lupa)),
so encoding, decoding and the import's layout merge behave exactly as they do in game. The
Edit Mode and ElvUI tools are pure Python.

## Setup

From the repository root:

```bash
just setup
```

That creates `wow/tools/.venv`, installs lupa into it and fetches the Lua sources. By hand:

```bash
cd wow/tools
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./fetch_deps.sh      # EllesmereUI and LibDeflate Lua sources into .deps/ (gitignored)
```

You need Python 3.10 or newer, git and bash. CI uses Python 3.13. Set `EUI_DEPS` to keep the
Lua sources somewhere other than `.deps/`. `verify.sh` uses `$PYTHON` if set, then `.venv`,
then `python3`.

## Scripts

| Script | Purpose |
| --- | --- |
| `euilib.py` | Shared helpers: the Lua runtime, `DecodeEUI`, `EncodeEUI` and a readable dump. |
| `eui_decode.py` | Decode `!EUI_` strings to `.lua` and `.json`. Prints the payload type, client, UI scale and modules, and warns if the string is a full account export. |
| `eui_make_retail.py` | Build `retail.txt` from `wow-forever.txt`. Also defines the retail only modules (Mythic+ Tools, Friends, Dragon Riding). |
| `eui_verify_layout.py` | Simulate the import's layout merge (`--client forever` or `retail`) and show which anchors apply. |
| `editmode_convert.py` | Convert a Forever Edit Mode layout to retail, or validate layouts with `--check`. |
| `elvui_decode.py` | Decode ElvUI `!E1!` strings to JSON. Pure Python. The ElvUI strings themselves are in the `legacy` tag. |
| `check_exports.py` | Enforce the rules for committed strings. See [Verifying](#verifying). |
| `verify.sh` | Run `check_exports.py` and every check below. CI runs this. |
| `fetch_deps.sh` | Fetch the pinned EllesmereUI and LibDeflate sources. |
| `legacy/build_eui_from_elvui.py` | The original ElvUI to EllesmereUI generator. Kept as a record of how each setting was mapped. Superseded: do not regenerate profiles from it. Not linted. |

The Python tools take `--help` (`legacy/` aside). Decoded output from `eui_decode.py` and `elvui_decode.py` lands
next to the input by default. It is gitignored, but `--out` into a temporary folder is tidier.

### How the Edit Mode conversion works

A layout string is a header then one ten token entry per system. Forever writes format
version 4, which adds an `interfaceStyle` field. The converter drops the Forever only systems
(26 MainActionBarEndCap, 27 GroupFinder, 29 SwingTimer), renumbers 28 LossOfControl to 26,
and writes a version 3 header. Every other system and settings enum is identical between the
two games. That was checked against Blizzard's generated docs in
[Gethe/wow-ui-source](https://github.com/Gethe/wow-ui-source) (`live` 12.1.0 build 69933,
`forever` 1.60.1 build 70124). Whether retail accepts the version 3 header is not yet
confirmed.

## Verifying

```bash
just verify          # or: wow/tools/verify.sh
```

`check_exports.py` checks that:

- every string file is one line of printable ASCII with no trailing newline
- EllesmereUI strings decode to a profile export (`type=full`), never a full account export
- Edit Mode layouts parse and match their header's system count
- no decoded `.lua` or `.json` output is tracked under `wow/`

Then `verify.sh` runs the handover checks, from `wow/tools/`:

```bash
python3 eui_decode.py ../ellesmereui/wow-forever.txt ../ellesmereui/retail.txt --out /tmp/eui
python3 eui_make_retail.py ../ellesmereui/wow-forever.txt /tmp/eui/rebuilt.txt && cmp /tmp/eui/rebuilt.txt ../ellesmereui/retail.txt
python3 eui_verify_layout.py ../ellesmereui/wow-forever.txt --client forever
python3 eui_verify_layout.py ../ellesmereui/retail.txt --client retail
python3 editmode_convert.py ../blizz-ui/Craigtho-forever.txt /tmp/eui/em.txt && cmp /tmp/eui/em.txt ../blizz-ui/Craigtho-retail.txt
```

If a `cmp` fails, the retail file is stale and `verify.sh` names the command that rebuilds it.

## When to re-run the generators

`just regen` runs both generators and then verifies.

- **`eui_make_retail.py`**: whenever `wow-forever.txt` changes, or after editing the retail
  only modules in its `TRANSFORM` block.
- **`editmode_convert.py`**: whenever `Craigtho-forever.txt` changes. After a major patch,
  re-check both branches' `Blizzard_APIDocumentationGenerated/EditModeManagerConstants*Documentation.lua`
  in Gethe/wow-ui-source, and update `FOREVER_ONLY` and `RENUMBER` if the system IDs moved.

## Pinned sources

`fetch_deps.sh` pins the commits the tools were tested against:

| Source | Commit | Version |
| --- | --- | --- |
| [EllesmereUI](https://github.com/EllesmereGaming/EllesmereUI) | `acccae4163fc` | v9.3.3, 2026-09-29 |
| [LibDeflate](https://github.com/SafeteeWoW/LibDeflate) | `afc3b78d12fb` | 1.0.2 |

These may need bumping after an EllesmereUI or WoW update, for example if an import starts
failing in game or a newer EllesmereUI changes its profile format. To bump EllesmereUI:

1. Change `ELLESMEREUI_COMMIT` in `fetch_deps.sh` and run it.
2. Run `just verify`.
3. If a tool stops finding the code it runs, update the markers it looks for. `euilib.py` lifts
   the serialiser from `EllesmereUI_Profiles.lua` between `local Serializer = {}` and
   `EllesmereUI._Serializer = Serializer`, and `eui_verify_layout.py` runs everything above
   `--  Profile DB helpers` plus `EllesmereUI.PayloadFromOtherClient`. `DecodeEUI` expects
   payload version 3.
4. If the rebuilt `retail.txt` differs only because the new serialiser encodes differently,
   run `just regen` and commit the result.

## Linting

`just lint` runs ruff with [`ruff.toml`](./ruff.toml) over this folder (excluding `legacy/`
and `.deps/`), plus the repository wide checks in `.github/scripts/lint.sh`.
`requirements-dev.txt` pins the ruff version CI uses.
