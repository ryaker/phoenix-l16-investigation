# 04b — Tone and Geometry Panels

---

## Tone Panel

Accessed by pressing `T` or clicking "Tone" in the editor mode selector.

### Layout

```
┌────────────────────────────────┐
│  TONE                          │
│                                │
│  White Balance                 │
│  [As Shot]  [Daylight]  [Shade]│
│  Temp ─────────────●── 6500K  │
│  Tint ──────●──────────  +12  │
│                                │
│  ── Exposure ──                │
│  Exposure ──────●───────  +0.3 │
│  Contrast ──────●───────    0  │
│  Highlights ────────●────  -25 │
│  Shadows ───────●────────  +15 │
│  Whites  ───────●────────    0 │
│  Blacks  ──────●─────────   -5 │
│                                │
│  ── Presence ──                │
│  Clarity ───────●────────  +15 │
│  Vibrance ──────●────────  +20 │
│  Saturation ────●────────    0 │
│                                │
│  [Reset Tone]                  │
└────────────────────────────────┘
```

### White Balance

Two rows:

**Preset buttons:** `As Shot` | `Auto` | `Daylight` | `Cloudy` | `Shade` | `Tungsten` | `Fluorescent`

- "As Shot": uses the factory AWB gains from the LRI header (default)
- "Auto": triggers a pipeline-computed auto white balance
- Others: preset Kelvin values (Daylight=5500K, Cloudy=6500K, Shade=7500K, Tungsten=3200K, Fluorescent=4000K)

**Sliders:**
- **Temp**: 2000K–12000K. Shows color: left end blue (cool), right end orange (warm).
- **Tint**: -150 to +150. Shows color: left end green, right end magenta.

Moving either slider automatically deselects the preset buttons (shows as custom).

### Exposure Sliders

| Slider | Range | Default |
|--------|-------|---------|
| Exposure | -3.0 EV to +3.0 EV | 0.0 |
| Contrast | -100 to +100 | 0 |
| Highlights | -100 to +100 | 0 |
| Shadows | -100 to +100 | 0 |
| Whites | -100 to +100 | 0 |
| Blacks | -100 to +100 | 0 |

Double-click any slider to reset it to its default value.

### Presence Sliders

| Slider | Range | Default |
|--------|-------|---------|
| Clarity | -100 to +100 | 0 |
| Vibrance | -100 to +100 | 0 |
| Saturation | -100 to +100 | 0 |

### Reset Tone

Resets all tone parameters to defaults and sets White Balance back to "As Shot". Adds one undo step. Requires no confirmation.

### Live Preview During Editing

Tone adjustments trigger a low-res re-render. The canvas updates as the user drags sliders. Because tone is applied post-fusion (the last stage of the pipeline), tone re-renders are significantly faster than full re-renders:

- Target: < 500ms per tone adjustment at preview resolution
- Canvas shows previous state until new render arrives
- No spinner for tone changes unless render takes > 500ms

---

## Geometry Panel

Accessed by clicking "Geometry" in the editor mode selector. (There is no keyboard shortcut — Geometry is used infrequently.)

### Layout

```
┌────────────────────────────────┐
│  GEOMETRY                      │
│                                │
│  ── Crop ──                    │
│  [Original] [1:1] [4:3] [16:9] │
│  [3:2]      [5:4] [Custom]     │
│                                │
│  Drag crop handles on image    │
│                                │
│  W: [10432]  H: [7824]         │
│                                │
│  ── Rotation ──                │
│  ↺ ─────────●──────────── ↻   │
│  -45°              Angle: 0.0° │
│                                │
│  ── Flip ──                    │
│  [↔ Flip H]   [↕ Flip V]       │
│                                │
│  [Reset Geometry]              │
└────────────────────────────────┘
```

### Crop

**Aspect ratio presets:** Original (10432:7824 = 4:3) | Square (1:1) | 4:3 | 16:9 | 3:2 | 5:4 | Custom

Selecting a preset:
- Canvas shows crop overlay (dimmed outside crop, bright inside)
- Handles at corners and edges of crop rect
- Drag handles to adjust; aspect ratio locked unless "Custom" is selected
- Drag inside the crop rect to reposition

In Custom mode, both W and H fields are editable. Width and height shown in pixels at full resolution.

**No crop indicator in other panels:** When a crop is active, a subtle icon appears in the status bar ("Cropped: 8000×6000") to remind the user.

### Rotation

Slider: -45° to +45°, default 0°.

- Moving the slider rotates the canvas in real-time (GPU transform, no re-render needed)
- Re-render triggered when slider is released
- Canvas automatically expands/contracts crop to avoid black corners at non-zero rotation (auto-crop within image bounds)

The angle value field accepts keyboard input. Type a number and press Return.

### Flip

Two buttons:
- **Flip Horizontal**: Mirror left/right. Toggle — active state shown with filled button.
- **Flip Vertical**: Mirror top/bottom. Toggle.

Both can be active simultaneously (= 180° rotation, which is distinct from 180° rotation because flips are spatial, not just rotational).

Flip is instantaneous (GPU transform, no re-render).

### Reset Geometry

Removes crop, sets rotation to 0°, clears both flips. Adds one undo step.

---

## Interaction Between Tone/Geometry and Other Panels

Tone and geometry changes are visible in all panels. The depth overlay and refocus tools continue to function on top of tone-adjusted and geometrically-cropped renders.

The order of operations in the pipeline is:
1. Per-camera ISP (fixed, not adjustable)
2. Multi-camera fusion (fixed)
3. Depth map (used by depth tools and refocus)
4. Geometry (crop, rotation, flip)
5. Tone (WB, exposure, etc.)
6. Output

From the UI's perspective, the user can adjust steps 3, 4, and 5 in any order and the pipeline re-renders with all adjustments applied.
