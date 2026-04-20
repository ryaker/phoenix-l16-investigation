# 04 — Editor View

---

## Purpose

The Editor is the main working space. The user lands here by double-clicking a photo in the Library. It shows the processed image and provides access to all editing tools.

The Editor has its own internal mode that determines which tools are active. The mode switcher is in the right panel header.

---

## Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  TOOLBAR                                                             │
│  [←] [→]  [Library | Editor ●]  ──────  [Fit] [1:1] [±]  [Export] │
├──────────────┬──────────────────────────────────┬───────────────────┤
│  LEFT PANEL  │                                  │  RIGHT PANEL      │
│  (Filmstrip) │          CANVAS                  │  (Edit Controls)  │
│              │                                  │                   │
│  [thumb]     │                                  │  [Mode: Refocus]  │
│  [thumb ●]   │      Full-size image preview     │  ─────────────    │
│  [thumb]     │      (Metal-accelerated)         │  Refocus          │
│  [thumb]     │                                  │  Depth Tools      │
│  [thumb]     │      Overlay: depth map          │  Tone             │
│  [thumb]     │      Overlay: focus point        │  Geometry         │
│  [thumb]     │                                  │  ─────────────    │
│              │                                  │  [controls for    │
│              │                                  │   active mode]    │
│              │                                  │                   │
│              │                                  │  ─────────────    │
│              │                                  │  [Histogram]      │
└──────────────┴──────────────────────────────────┴───────────────────┘
│  STATUS BAR: L16_02532.lri  ·  10432 × 7824  ·  Processing…  ██░░  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Canvas

The canvas is the large central area showing the photo. It is Metal-accelerated — the pipeline delivers pixel data as a Metal texture and the canvas composites layers on top without CPU readback.

### Canvas Layers (bottom to top)

1. **Image layer**: The processed photo. Updated asynchronously as the pipeline renders.
2. **Depth overlay**: An optional translucent false-color visualization of the depth map. Toggled by `Cmd+D` or the Show Depth Overlay button.
3. **Mask overlay**: When using depth editing tools, shows the current brush stroke or lasso selection.
4. **Focus indicator**: When in Refocus mode, shows where the focus plane is as a subtle highlight on in-focus areas.
5. **UI chrome**: Crop handles, zoom controls, cursor.

### Canvas Interactions

| Gesture / Key | Action |
|---------------|--------|
| Scroll | Zoom in/out (centered on cursor) |
| Pinch (trackpad) | Zoom |
| Click+drag (hand cursor) | Pan when zoomed in |
| Cmd+0 | Zoom to fit |
| Cmd+1 | Zoom 1:1 |
| Click (Refocus mode) | Set focus point |
| Click+drag (Brush mode) | Paint depth correction |
| Click+drag (Lasso mode) | Draw lasso selection |

### Render States

The canvas shows different content depending on pipeline state:

| State | Canvas shows |
|-------|-------------|
| Never rendered | Embedded LRI preview (low-res, possibly quite small — may show as blurry center crop) |
| Rendering in progress | Last completed render (if any), with a spinner in the status bar |
| Render complete | Full-resolution processed image |
| Edits pending re-render | Slightly desaturated / blurred image, spinner active |

The user never sees a blank canvas. There is always something to look at.

---

## Right Panel — Edit Controls

The right panel has a **mode selector** at the top and **mode-specific controls** below.

### Mode Selector

A horizontal segmented control with four modes:

```
[Refocus] [Depth] [Tone] [Geometry]
```

Keyboard shortcuts: `R` = Refocus, `D` = Depth, `T` = Tone, `G` = not used here (G = Library).

The mode selector controls:
- Which controls appear in the right panel below
- Which cursor/interaction is active on the canvas
- Whether overlays are shown on the canvas

### Bottom of Right Panel — Histogram

Always visible at the bottom of the right panel, regardless of mode.

Shows:
- RGB histogram of the rendered image
- Clipping indicators (triangles at top-left and top-right corners of histogram)
- Exposure value (EV) readout

---

## Left Panel — Filmstrip

The filmstrip shows thumbnails of all photos in the same folder as the current photo, in the same sort order as the Library view.

- Scroll direction: vertical (default) or horizontal (user preference)
- Current photo is highlighted with a colored border
- Click a thumbnail to navigate to that photo
- Each thumbnail shows the same status badge as in Library view

The filmstrip does not reload from disk while the user is editing — it uses cached thumbnails. A "Refresh" button at the top refreshes if new photos have been imported.

---

## Processing Lifecycle in the Editor

When the user opens a photo in the Editor for the first time:

```
1. Canvas shows: embedded LRI preview (immediate)
2. Pipeline: begins low-resolution render (preview quality, ~2 MP)
3. Canvas shows: low-res render when complete (fast, ~2-5 seconds)
4. Status bar: "Preview ready — rendering full resolution…"
5. Pipeline: begins full-resolution render (81.6 MP, ~30-120 seconds depending on hardware)
6. Canvas shows: full-res render when complete, zoom in becomes crisp
7. Status bar: idle
```

If the user makes an edit during step 5, the full-res render is cancelled and restarts after the edit.

When the user navigates to a photo they have opened before:
- If a full-res render is cached: shows immediately (step 6 state)
- If only a low-res render is cached: shows low-res, begins full-res render from step 4
- Depth map is loaded from cache alongside the render

Renders are cached per-LRI in the app's cache directory. Cache is evicted LRU when it exceeds the user's configured limit (default 10 GB).

---

## Undo/Redo

The undo stack is per-photo. Navigating to a different photo does not clear the undo stack of the previous photo.

What is undoable:
- Depth brush strokes (each stroke is one undo step)
- Lasso selections and operations (each operation is one undo step)
- Quick select masks (each application is one undo step)
- Face matting on/off toggle
- Focus point changes (Refocus mode)
- Aperture value changes (Refocus mode)
- Tone adjustments
- Crop/rotation

What is NOT undoable:
- Export operations
- Import operations
- Library organization

Undo history is preserved in the `.lrp` sidecar and persists across sessions (up to 50 steps per photo).

---

## Cursor States

The cursor changes to communicate the active tool:

| Mode | Canvas cursor |
|------|--------------|
| Refocus (no active tool) | Crosshair (click to set focus) |
| Depth Brush | Circle with adjustable radius |
| Depth Lasso | Lasso cursor |
| Depth Quick Select | Magic wand / sparkle cursor |
| Depth Heal | Bandage / heal cursor |
| Zoom | Magnifying glass (with +/-) |
| Pan | Open hand / closed hand |

---

## Zoom Level Indicator

In the top-right corner of the canvas (not the toolbar), a small floating indicator shows the current zoom level ("Fit", "25%", "50%", "100%", "200%").

This indicator fades out 2 seconds after the last zoom change.
