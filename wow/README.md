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
| [`blizz-ui/Craigtho-retail.txt`](./blizz-ui/Craigtho-retail.txt) | Retail | **Generated** from `Craigtho-forever.txt`. Format version 2 (the one retail imports), 52 systems. |
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

The retail layout uses format version 2, the version retail itself exports. An earlier
conversion wrote version 3, which is a Forever format, and retail refused to import it. If
an import ever fails again, export a native layout from retail and compare its header with
`Craigtho-retail.txt`.

### Keybinds

With the game closed, copy `wow/Bindings.wtf` to `WTF\Account\<ACCOUNT>\bindings-cache.wtf`
inside that game's install folder, where `<ACCOUNT>` is your account's folder name. It replaces
every bind, so back up the existing file first.

| Game | Install folder |
| --- | --- |
| Retail | `World of Warcraft\_retail_` |
| Forever (beta, client 1.60.1) | `World of Warcraft\_classic_beta_` |

From WSL, for Forever (the game writes these files with CRLF endings, so match it):

```bash
acct="/mnt/c/Program Files (x86)/World of Warcraft/_classic_beta_/WTF/Account/<ACCOUNT>"
cp "$acct/bindings-cache.wtf" "$acct/bindings-cache.wtf.bak"
sed 's/$/\r/' wow/Bindings.wtf > "$acct/bindings-cache.wtf"
```

Every Blizzard command in the file exists on Forever 1.60.1 (checked against its
`Bindings_Camelot.xml`). The few `CLICK` lines belong to old addons (ConsolePort, Bartender4,
WoW-Pro) and do nothing without them. A character with **Character Specific Keybindings**
turned on keeps its own `bindings-cache.wtf` in its character folder, which overrides the
account file.

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
