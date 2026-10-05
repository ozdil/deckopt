# Contributing and Security Standards

This project is an independent open-source autonomous optimization engine engineered strictly for Valve Steam Deck hardware (LCD/OLED) running SteamOS 3.x.

## Security and Engineering Principles

1. **Hardware Safety Limits:**
   - Thermal Design Power (TDP): Strictly clamped between 3W and 15W.
   - GPU Clock Frequency: Constrained between 200MHz and 1600MHz.
   - Refresh Rates: Maximum 60Hz on LCD panels, 90Hz on OLED panels.
   - Frame Pacing: Exact integer divisor requirement (`refresh_hz % fps_limit == 0`).
2. **User Isolation and Privacy:**
   - API keys and profiles are stored locally on-device under `user://` with strict `0600` permissions.
   - Direct client-to-Google HTTPS endpoints; zero intermediate telemetry servers.
3. **Typography and Style:**
   - Default typography: `JetBrainsMono Nerd Font, JetBrains Mono, monospace`.
   - Zero-Emoji Policy: Absolutely zero unicode emojis in code, commits, or documentation.
   - Primary language for GitHub repository documentation: US English (`en-US`).
