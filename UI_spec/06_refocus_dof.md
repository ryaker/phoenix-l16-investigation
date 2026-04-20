# 06 — Virtual Refocus and Depth-of-Field

---

## The Signature Feature

Post-capture refocus is the thing that makes the L16 unique. Every other L16 feature could be found in other cameras. This cannot.

The L16 captures everything in sharp focus (each module at f/2.0 or f/2.4, fixed). The pipeline synthesizes a configurable depth of field from the depth map. The user can:

1. **Choose where to focus** — click on anything in the image and the simulated focus plane moves there
2. **Choose how much blur** — set a virtual aperture (f-stop equivalent) from fully sharp to extreme portrait blur

This is not a lens blur filter. It is a depth-map-driven per-pixel bokeh simulation. Objects at the focus distance are sharp. Objects closer or farther are blurred in proportion to their depth distance from the focus plane.

---

## Accessing Refocus Controls

1. Press `R` or click the "Refocus" tab in the right panel
2. The canvas enters refocus mode (cursor changes to crosshair)
3. The focus ring overlay appears around the current focus point
4. Right panel shows refocus controls

---

## Right Panel — Refocus Controls

```
┌────────────────────────────────┐
│  REFOCUS                       │
│                                │
│  Focus Point                   │
│  [Click image to set]          │
│  ○ Current: 2.4m               │
│                                │
│  Virtual Aperture              │
│  f/∞ ──────●────────── f/1.4   │
│                f/4.0           │
│                                │
│  ── Quick Presets ──            │
│  [Sharp]  [Portrait]  [Bokeh]  │
│                                │
│  ── Advanced ──                │
│  [ ] Tilt Focus                │
│  Bokeh shape: [●] [●] [⬡] [★]  │
│                                │
│  [Reset to Sharp]              │
└────────────────────────────────┘
```

---

## Focus Point

**Interaction:** Click anywhere on the canvas in Refocus mode to set the focus point to that location.

**What happens:**
- The pipeline reads the depth value at the clicked pixel
- That depth becomes the focus distance
- The image re-renders with the new focus distance (at the current aperture setting)

**Visual feedback on canvas:**
- A subtle circular ring appears at the clicked location, animates briefly, then fades
- The in-focus region is highlighted with a very subtle edge glow (optional, toggle in preferences)

**Focus distance display:**
- If the pipeline provides metric depth (meters), the panel shows "Current: 2.4m"
- If only relative depth is available, shows "Current: midground" or similar label derived from relative depth buckets
- Shows always as a read-only value next to "Focus Point"

---

## Virtual Aperture Slider

A horizontal slider from f/∞ (fully sharp, no blur) on the left to f/1.4 (maximum blur) on the right.

**f-stop scale:** f/∞, f/22, f/16, f/11, f/8, f/5.6, f/4, f/2.8, f/2, f/1.4

The slider uses a non-linear scale — the higher-blur end (below f/4) has more visual resolution because that's where most user interaction happens for portraits.

**Current value display:** Shows the selected f-stop numerically below the slider (e.g., "f/4.0").

**Live preview:** Moving the slider triggers a low-resolution preview re-render. The preview updates with each slider stop position, or at most every 500ms while dragging. Full-resolution re-render happens when the slider is released (or after a 1-second idle period after release).

**The slider at f/∞:** No blur applied. Equivalent to "show everything sharp." This is useful for inspecting image sharpness, checking corner focus, and exporting a fully-sharp version.

---

## Quick Presets

Three one-click buttons for common use cases:

| Button | Effect |
|--------|--------|
| **Sharp** | Sets aperture to f/∞ (no blur). Focus point unchanged. |
| **Portrait** | Sets aperture to f/2.0. Focuses on nearest face if detected, else center. |
| **Bokeh** | Sets aperture to f/1.4 (maximum blur). Focus on current focus point. |

Presets apply immediately and add one undo step.

---

## Tilt Focus (Advanced)

A checkbox: **Tilt Focus**

When enabled, the focus plane is no longer a flat plane at a fixed depth — it can be tilted (like tilt-shift photography). Two handle points appear on the canvas when Tilt Focus is active:

- One handle at the near end of the focus plane
- One handle at the far end of the focus plane
- Drag either handle to tilt the focus plane

The pipeline recalculates the per-pixel blur distances based on the tilted plane geometry.

This is an advanced feature. Hidden behind the "Advanced" disclosure triangle. Users who don't know what it is don't see it.

---

## Bokeh Shape

When aperture is set to f/4.0 or lower (meaningful blur present), the bokeh shape selector appears:

Four shape options:
- **Round** (default): circular bokeh (most natural)
- **Slightly hexagonal**: realistic multi-blade aperture look
- **Hexagonal**: stylized hexagonal bokeh
- **Star**: artistic star-burst bokeh

The shape only affects out-of-focus highlights (specular bokeh). The overall blur amount is unchanged.

This is in the "Advanced" disclosure section.

---

## Reset to Sharp

A button at the bottom of the panel. Sets aperture to f/∞. Does not change the focus point. Adds one undo step.

---

## Focus Ring Animation

When the user clicks a new focus point, the canvas shows a brief animation:
- A ring expands from the click point and fades
- Duration: 0.4 seconds
- Does not interfere with immediate re-render trigger

---

## Refocus Preview Performance

Post-capture refocus requires the pipeline to re-render the depth-of-field blur whenever focus point or aperture changes. This is the most computationally expensive interactive operation.

**Target performance:**
- Low-res preview (1/4 resolution): < 500ms on target hardware (Apple M1 and later)
- Full-resolution render: < 30 seconds on target hardware

**UI behavior during re-render:**
- The canvas shows the previous render with a subtle loading indicator in the corner
- The slider and focus controls remain interactive (user can adjust while rendering)
- If the user makes a second change before the first render completes, the first render is cancelled

**Cache:** Renders for specific (focus-distance, aperture) combinations are cached. If the user returns to a previously-used setting, the cache is checked before re-rendering.

---

## Exporting Refocus Variants

The user may want multiple exports of the same photo at different focus settings. This is supported via the export queue — see `07_export.md` for details.

Example workflow:
1. Set focus to subject, f/2.0 → Add to Export Queue as "portrait.jpg"
2. Set aperture to f/∞ → Add to Export Queue as "sharp.jpg"
3. Export queue runs both in the background

---

## Underlying Pipeline Contract

| What UI needs | Pipeline provides |
|--------------|-------------------|
| Depth value at a pixel | `getDepthAtPoint(x, y) → float` |
| Re-render with new focus/aperture | `setFocusDistance(depth); setAperture(fstop); render()` |
| Face detection for Portrait preset | `detectFaces() → [FaceRect]` |
| Tilt-focus plane support | `setFocusPlane(normal, distance)` |
| Bokeh shape parameter | `setBokehShape(enum)` |

The UI does not implement any bokeh math. It passes parameters to the pipeline and displays what comes back.
