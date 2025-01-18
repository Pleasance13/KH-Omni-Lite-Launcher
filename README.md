# KINGDOM HEARTS Omni Lite Launcher - Guide (Windows Only)

This guide will walk you through setting up the KINGDOM HEARTS Omni Lite Launcher. The launcher allows you to launch Kingdom Hearts games via Heroic Games Launcher, using either an all-in-one launcher or simple command-line arguments and Steam shortcuts.

---

## Requirements

- **Heroic Games Launcher**: Installed and set up with your Kingdom Hearts games.

---

## Setup Instructions

### 1. Place the Files

1. Unpack the provided files to a convenient directory on your system, such as:
   ```
   ~/Games/KINGDOM HEARTS Omni Lite Launcher/
   ```

### 2. Launch `KINGDOM HEARTS Omni Lite Launcher.exe`

Launch `KINGDOM HEARTS Omni Lite Launcher.exe` once and it will prompt you to set the paths to your game installation folders, `Heroic.exe`, and Heroic's `GamesConfig` path. 

You don't need to have all games installed. If any are not, simply cancel that prompt and continue. With the paths set, you can now use the launcher! The launcher can be controlled with either a mouse, a keyboard (**ARROW** keys to move, **SPACE** to select, **ESC** to exit), or a gamepad (**✜** to move, **Ⓐ** (Xbox)/**Ⓧ** (PlayStation) to select.

**F11** or **Alt+Enter** will toggle fullscreen, or you can add `-f` to the launch arguments to start it in fullscreen mode.

If you wish to launch the games directly and separately, continue to step 3.

### 3. Add Non-Steam Games

1. Open Steam.
2. Go to **Library > Add a Game > Add a Non-Steam Game**.
3. Browse and select a `KINGDOM HEARTS Omni Lite Launcher.exe`
4. Add it to your library and then in the properties of the new game entry, enter one of the following launch arguments.
   ```
   -kh1
   -com
   -kh2
   -bbs
   -ddd
   -afp
   -kh3
   ```
5. Repeat for each game you wish to add.

### 5. Test the Setup

1. Launch any game from Steam.
2. If everything is configured correctly, the game should launch through Heroic Games Launcher.

---

## Troubleshooting

### Game Does Not Launch
- Double-check the paths in `LauncherConfig.json` (This file is created when you first run `KINGDOM HEARTS Omni Lite Launcher.exe` and choose your paths. It can be found wherever you put the EXE).
- Ensure Heroic Games Launcher is installed and configured.
- You may need to ensure Heroic creates the game's config file by opening Heroic and changing any setting on the game.

### I've installed more of the games since the initial setup. How do I add their install paths?
- You can either manually edit `LauncherConfig.json` or delete it and re-run `KINGDOM HEARTS Omni Lite Launcher.exe`.
