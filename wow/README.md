# World of Warcraft UI

Craig's UI for WoW Forever and retail: an [EllesmereUI](https://github.com/EllesmereGaming/EllesmereUI)
profile, a Blizzard Edit Mode layout and a keybinds file. Forever is the source of truth. The
retail files are generated from it by the [tools](./tools/README.md), so both games share one
layout and look.

## Files

| File | Game | What it is |
| --- | --- | --- |
| [`ellesmereui/wow-forever.txt`](./ellesmereui/wow-forever.txt) | Forever | EllesmereUI profile, exported in game. **Source of truth.** 15 modules, UI scale 0.64. |
| [`ellesmereui/retail.txt`](./ellesmereui/retail.txt) | Retail | **Generated** from `wow-forever.txt`. 18 modules: adds Mythic+ Tools, Friends list and Dragon Riding, and drops the Forever only parts. |
| [`blizz-ui/Craigtho-forever.txt`](./blizz-ui/Craigtho-forever.txt) | Forever | Edit Mode layout, format version 4, 59 systems. **Source of truth.** |
| [`blizz-ui/Craigtho-retail.txt`](./blizz-ui/Craigtho-retail.txt) | Retail | **Generated** from `Craigtho-forever.txt`. Format version 3, 53 systems. |
| [`Bindings.wtf`](./Bindings.wtf) | Both | Keybinds, including the stance bar. Matches this layout on both games. |
| [`tools/`](./tools) | | Python tools that decode, generate and verify the strings. |

Modules in both profiles: Action Bars, Aura Buff Reminders, Bags, Chat, Cooldown Manager,
Damage Meters, Data Bars, Minimap, Nameplates, QoL, Quest Tracker, Quickdraw, Raid Frames,
Resource Bars and Unit Frames. Retail adds Mythic+ Tools (`MythicTimer`), Friends and Dragon
Riding.

## Restoring the UI

Use the Forever files on WoW Forever and the retail files on retail. Each string is one long
line: copy the whole file. On GitHub, the **Copy raw file** button does this in one click.

### EllesmereUI profile

1. Install EllesmereUI and finish the first install popups.
2. Type `/eui`, open **Profiles & Presets** and choose **Import Profile**.
3. Paste the string: `wow-forever.txt` on Forever, `retail.txt` on retail.
4. Name the profile and choose **Match Scale** (0.64).
5. Reload the UI.

### Edit Mode layout

1. Press Esc and open **Edit Mode**.
2. Choose **Import** from the layout menu.
3. Paste `Craigtho-forever.txt` on Forever, or `Craigtho-retail.txt` on retail.

Whether retail accepts the converted layout's version 3 header is not yet confirmed. If
retail rejects it, set the layout up in game on retail and export a native retail layout
instead.

### Keybinds

With the game closed, copy `wow/Bindings.wtf` to `WTF\Account\<ACCOUNT>\bindings-cache.wtf`
inside that game's install folder, where `<ACCOUNT>` is your account's folder name.

### Set in game

The profile strings do not carry these, so set them by hand:

| Setting | Notes |
| --- | --- |
| Threat meter | Account wide. Show it with `/euitm show`. |
| Tooltip position | Account wide. |
| Cooldown Manager spells | Per spec. |
| Tracking Bar spells | Per spec. |
| Buff Reminders custom spells | For example Battle Shout. |
| Friends window background | An account wide window skin setting. |

## Changing the UI

Make shared changes on Forever, then regenerate retail.

1. Change the UI in game on Forever and export the EllesmereUI profile or the Edit Mode layout.
2. Replace `ellesmereui/wow-forever.txt` or `blizz-ui/Craigtho-forever.txt` with the export.
   Save it as a single line with **no trailing newline**. From WSL, for example:

   ```bash
   powershell.exe -NoProfile -Command Get-Clipboard | tr -d '\r\n' > wow/ellesmereui/wow-forever.txt
   ```

3. Run `just regen` to rebuild the retail files, which also runs `just verify`.
4. Commit the Forever file and the regenerated retail file together.

Two things to know:

- **Retail files are generated.** Changes made in game on retail are lost the next time retail
  is rebuilt. The retail only modules (Mythic+ Tools, Friends, Dragon Riding) are defined in
  [`tools/eui_make_retail.py`](./tools/eui_make_retail.py), so change them there.
- **Commit profile exports only.** An EllesmereUI full account export carries character gold,
  bag contents and click cast bindings, and this repository is public. `just verify` fails on
  one, and `tools/eui_decode.py` prints the type (`type=full` is a profile export).
