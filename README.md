# deckopt: AI-Driven Autonomous Game Optimization Engine for Valve Steam Deck (Alpha v0.1.0)

[![Release](https://img.shields.io/github/v/release/ozdil/deckopt?include_prereleases)](https://github.com/ozdil/deckopt/releases)
[![Platform](https://img.shields.io/badge/platform-SteamOS%203.x%20%7C%20Steam%20Deck-1a9fff)](https://store.steampowered.com/steamdeck)
[![Engine](https://img.shields.io/badge/engine-Godot%204.7-478cbf)](https://godotengine.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**deckopt** is an autonomous, on-device AI-powered performance tuning and game optimization engine engineered specifically for Valve Steam Deck hardware (LCD "Jupiter" and OLED "Galileo") running SteamOS 3.x.

It eliminates the tedious trial-and-error process of manually researching TDP limits, GPU clocks, FSR configurations, and Proton launch flags on forums. By leveraging Google Gemini 2.5 Flash and strict deterministic hardware safety boundaries, `deckopt` calculates optimal, battery-conscious per-game profiles with zero guesswork.

> **Hardware Enforced:** This software strictly operates on authentic Valve Steam Deck hardware. Running it on non-Deck environments triggers a BIOS-level hardware lock that halts execution safely.

---

## Architecture Overview

```
+-------------------------------------------------------------------------+
|                  Valve Steam Deck (SteamOS 3.x / Gamescope)              |
+-------------------------------------------------------------------------+
       |                                                    |
       v                                                    v
 [Internal NVMe / MicroSD]                           [DMI BIOS Validation]
 Appmanifest ACF Parsing                          (Jupiter LCD / Galileo OLED)
       |                                                    |
       +--------------------+-------------------------------+
                            |
                            v
               +---------------------------+
               |  Godot 4.7 Gamepad UI     |
               |  (1280x800, D-Pad Nav)    |
               +---------------------------+
                            |
                            v
               +---------------------------+
               |  Secure Local Storage     |  <-- user://gemini.key (0600)
               |  Profile & Store Engine   |  <-- user://profiles.json (0600)
               +---------------------------+
                            |
                            | (HTTPS REST / Game Name + AppID + Target SoC)
                            v
               +---------------------------+
               |  Google Gemini 2.5 Flash  |
               +---------------------------+
                            |
                            v (Structured JSON Payload)
               +---------------------------+
               | Deterministic Sanitizer   |  <-- TDP: [3, 15] W
               |  (profile.gd Hardware Cap)|  <-- GPU: [200, 1600] MHz
               +---------------------------+  <-- FPS: Frame Pacing Divisor
                            |
                            v
        +----------------------------------------+
        | Final Recommended Profile & Parameters |
        | - Quick Access Menu Directives         |
        | - Steam Launch Options (To Clipboard)  |
        +----------------------------------------+
```

---

## Key Features and Technical Highlights

### 1. BIOS-Level Hardware Verification (`deck_scan.gd`)
- Reads `/sys/devices/virtual/dmi/id/product_name`.
- Strictly targets `jupiter` (Steam Deck LCD, AMD Aerith 7nm APU, 60Hz) and `galileo` (Steam Deck OLED, AMD Sephiroth 6nm APU, 90Hz).
- Automatically discovers installed titles across both internal storage (`~/.local/share/Steam/steamapps`) and MicroSD cards (`/run/media/mmcblk0p1/steamapps`).

### 2. Hybrid AI Engine (`gemini.gd`)
- Queries Google Gemini 2.5 Flash to compute optimal thermal, rendering, and frame pacing parameters based on game engine characteristics and Deck hardware specs.
- **Client-Side Privacy:** Your Gemini API key is stored strictly on-device under `user://gemini.key` with `0600` permissions. It is never relayed through third-party telemetry servers.

### 3. Deterministic Safety Boundaries (`profile.gd`)
LLM outputs are inherently probabilistic and cannot be trusted directly with hardware governance. Every AI-generated profile must pass through deterministic bounding filters:
- **TDP Clamping:** Hard-clamped within `[3, 15]` Watts.
- **GPU Clock Limits:** Constrained between `[200, 1600]` MHz.
- **Mathematical Frame Pacing:** Target frame rates must be an exact integer divisor of the panel refresh rate (`refresh_hz % fps_limit == 0`) to prevent micro-stuttering (e.g., 30 FPS or 60 FPS on 60Hz LCD; 30, 45, or 90 FPS on 90Hz OLED).
- **Flag Allowlist:** Shell commands are strictly filtered. Only verified Proton/Mesa/Vulkan flags (`PROTON_USE_WINED3D`, `DXVK_ASYNC`, `DXVK_FRAME_RATE`, `WINE_FULLSCREEN_FSR`, `mesa_glthread`) are allowed. Command injectors (`;`, `&`, `|`, `` ` ``) are stripped immediately.

### 4. Gamepad-Native Interface (`main.gd`)
- Built in **Godot 4.7 Engine**, rendered natively at 1280x800 for the Steam Deck display.
- Seamless D-Pad and controller navigation out-of-the-box (A: Select, B: Back, D-Pad: Navigate).
- Single-click clipboard copying for launch options and asynchronous cancel safety during batch optimizations.

---

## One-Line Installation (Steam Deck)

Switch to **Desktop Mode** on your Steam Deck, open **Konsole**, and paste:

```bash
curl -fsSL https://github.com/ozdil/deckopt/releases/latest/download/install.sh | bash
```

### What This Script Does:
1. Validates that the host machine is an authentic Steam Deck (Jupiter/Galileo).
2. Downloads the latest verified release and validates its SHA256 checksum.
3. Installs the standalone executable into `~/Applications/deckopt/`.
4. Registers `deckopt` directly into your Steam Library as a "Non-Steam Game" via `steamos-add-to-steam`.

Return to **Gaming Mode**, and `deckopt` will be waiting under your **Non-Steam** library tab.

---

## Usage Workflow

1. **Enter API Key:** On first launch, enter your free Google Gemini API key (accessible via [Google AI Studio](https://aistudio.google.com/)). Press `Steam + X` to toggle the virtual keyboard.
2. **Batch Optimize:** Click **Optimize All Games**. The engine scans your library and caches optimal profiles locally.
3. **Apply Profile:** Select any game:
   - Apply the recommended Frame Limit, Refresh Rate, TDP, and GPU Clock via the Steam **Quick Access (...) > Performance** menu.
   - Click **Copy Launch Options to Clipboard** and paste the string into the game's **Properties > Launch Options**.

---

## Uninstallation

To remove `deckopt` completely from your Steam Deck:

```bash
curl -fsSL https://github.com/ozdil/deckopt/releases/latest/download/uninstall.sh | bash
```

Pass `-y` to clean user profiles and API keys without interactive confirmation.

---

## Contributing and Standards

- **Zero-Emoji Policy:** Strictly zero unicode emojis across code, documentation, and commits.
- **Typography:** Primary default font family is `JetBrainsMono Nerd Font, JetBrains Mono, monospace`.
- See [CONTRIBUTING.md](CONTRIBUTING.md) for full architecture and security guidelines.

## License

Released under the [MIT License](LICENSE).
