# RFC: Autonomous Dynamic Game Profiling and Deterministic Hardware Safety Layer for SteamOS

- **Author:** Ozan Ozdil (@ozdil)
- **Status:** Draft / Request for Comments
- **Target Repository:** ValveSoftware/SteamOS & ValveSoftware/gamescope
- **Reference Implementation:** [github.com/ozdil/deckopt](https://github.com/ozdil/deckopt)
- **Date:** October 2026

---

## 1. Summary

This RFC proposes an architectural pattern and an open platform interface for autonomous, title-specific performance tuning on handheld hardware (Valve Steam Deck LCD/OLED). 

Currently, achieving an optimal balance between battery longevity, thermal headroom, and smooth frame pacing requires manual user intervention via the Quick Access Menu (QAM). Users must manually research forum presets, tune TDP caps, adjust GPU clocks, configure upscalers (FSR), and enforce integer-divisor frame limits.

We present a hybrid paradigm: combining contextual large language model (LLM) inference for cold-start parameter estimation with a **strict, non-negotiable deterministic safety layer** that clamps all proposed parameters to hardware-safe boundaries. We propose standardizing an unprivileged D-Bus / IPC interface in SteamOS to allow authenticated user-space daemons or tools to safely query and stage performance profiles without root escalation.

---

## 2. Motivation and Problem Statement

Handheld gaming consoles are strictly power- and thermal-constrained environments:
- **TDP & APU Contention:** The AMD Aerith (7nm, LCD) and Sephiroth (6nm, OLED) APUs share a 15W package power limit. Unconstrained CPU execution often starves the RDNA 2 GPU cores, inducing sudden frame drops (micro-stutter) in modern titles.
- **Cognitive Overhead:** Casual users frequently run unoptimized defaults (15W flat, unconstrained clocks), reducing battery lifespan to under 90 minutes on titles that could comfortably achieve stable 40 FPS at 9-11W.
- **The Cold-Start Limitation of Crowdsourcing:** While static crowdsourced databases (such as ProtonDB or Decky community presets) are valuable, they suffer from lagging coverage on newly released games, day-one patches, and minor proton revisions.

An autonomous on-device inference layer can bridge this cold-start gap by deriving initial configurations from engine characteristics, graphics APIs, target resolution, and panel constraints.

---

## 3. The Deterministic Safety Invariant (Why LLMs Require Hardware Enclosure)

Generative AI models are probabilistic and inherently prone to hallucination. An unconstrained model might recommend a 25W TDP cap or a 2400 MHz GPU clock, which would risk hardware instability, thermal throttling, or kernel panics.

Therefore, the reference architecture enforces that **no raw model output is ever applied directly to hardware registers or runtime configurations**. All recommendations must pass through a hardcoded deterministic filter:

```
[ Raw LLM Output (JSON) ]
           |
           v
+-----------------------------------------------------------+
|             DETERMINISTIC SANITIZATION LAYER              |
+-----------------------------------------------------------+
| 1. TDP Clamping:        clamp(TDP, 3W, 15W)              |
| 2. GPU Clock Clamping:  clamp(Clock, 200MHz, 1600MHz)    |
| 3. Refresh Rate Cap:    LCD <= 60Hz, OLED <= 90Hz         |
| 4. Frame Pacing Rule:   Assert (Refresh_Hz % FPS_Cap == 0)|
| 5. Flag Allowlist:      Regex check against approved      |
|                         PROTON_* / DXVK_* variables only. |
+-----------------------------------------------------------+
           |
           v
[ Safe, Sanitized Profile ]
```

### Frame Pacing Divisor Constraint
To eliminate micro-stuttering caused by irregular frame pacing intervals (e.g., displaying 45 FPS on a 60 Hz display results in alternating 16.6ms and 33.3ms frames), the engine enforces that target frame limits must strictly divide the panel refresh rate:

$$\text{FPS}_{\text{target}} \in \{ x \in \mathbb{N} \mid \text{Refresh}_{\text{panel}} \pmod x = 0 \}$$

If an incompatible combination is proposed (e.g., 50 FPS on a 60 Hz LCD), the mathematical sanitizer automatically aligns the value to 30 FPS or adjusts the display refresh rate.

---

## 4. Proposed SteamOS Interface: `org.valvesoftware.SteamOS.PerformanceProfile`

Currently, adjusting TDP and GPU clock speeds outside the official Steam client UI requires root privileges (`sudo`, `pkexec`, or writing to sysfs attributes such as `/sys/class/drm/card0/device/pp_od_clk_voltage`). This creates an architectural security vulnerability when third-party tools request root elevation.

We propose exposing an unprivileged, authenticated D-Bus service managed by `steamos-polkit-helpers` or SteamOS session daemon:

### Proposed D-Bus Specification:

```xml
<!DOCTYPE node PUBLIC "-//freedesktop//DTD D-BUS Object Introspection 1.0//EN"
"http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd">
<node name="/org/valvesoftware/SteamOS/Performance">
  <interface name="org.valvesoftware.SteamOS.PerformanceProfile">
    <!-- Read current active limits -->
    <method name="GetActiveProfile">
      <arg name="profile" type="a{sv}" direction="out"/>
    </method>

    <!-- Stage a profile for an AppID with system-level validation -->
    <method name="StageProfileForApp">
      <arg name="appid" type="u" direction="in"/>
      <arg name="settings" type="a{sv}" direction="in"/>
      <arg name="status" type="b" direction="out"/>
    </method>

    <!-- Supported hardware limits reported by the kernel/SoC -->
    <property name="SupportedTdpRange" type="(uu)" access="read"/>
    <property name="SupportedGpuClockRange" type="(uu)" access="read"/>
    <property name="DisplayMaxRefreshRate" type="u" access="read"/>
  </interface>
</node>
```

### Architectural Benefits:
1. **Zero Root Privilege Requirement:** Third-party profilers, machine learning engines, and user-space daemons can stage per-game presets without executing elevated shell scripts.
2. **Atomic Verification:** The SteamOS daemon performs internal kernel-level clamping, ensuring that malicious or malformed parameters are dropped before touching the APU power table.
3. **Seamless Steam Overlay Sync:** Values set through the D-Bus interface immediately reflect in the QAM Performance overlay, preventing synchronization conflicts between Gamescope and external processes.

---

## 5. Reference Implementation

A fully functional, open-source reference implementation of this architecture has been developed and validated on SteamOS:
- **Repository:** [https://github.com/ozdil/deckopt](https://github.com/ozdil/deckopt)
- **Engine:** Godot 4.7 standalone client (1280x800 native resolution, Steam Input D-Pad navigation).
- **Inference Back-end:** Google Gemini 2.5 Flash via direct HTTPS REST (on-device API key storage with `0600` permissions).
- **Sanitization Core:** [godot/profile.gd](https://github.com/ozdil/deckopt/blob/main/godot/profile.gd)

---

## 6. Questions for the Valve & SteamOS Community

1. What are the team's thoughts on exposing an unprivileged, polkit-guarded D-Bus endpoint for QAM performance controls?
2. Would the SteamOS performance manager team consider integrating an open profile exchange schema (JSON-based) that external tuning engines and telemetry daemons could hook into?
3. How does the team envision the role of on-device ML/inference in future handheld SoC power balancing (e.g., dynamically predicting compute vs. render bottlenecks on heterogeneous cores)?

Feedback, critiques, and alternative architectural approaches are warmly welcome.
