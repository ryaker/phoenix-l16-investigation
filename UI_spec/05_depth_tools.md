# 05 — Depth Tools

---

## Why Depth Editing Exists

The L16 computes a depth map from multi-view stereo using the five 28mm camera modules. This depth map is what makes post-capture refocus possible: the pipeline uses it to simulate what the scene would look like at any arbitrary aperture and focus distance.

But the automatic depth map is imperfect. Depth estimation fails at:
- Object edges (foreground/background boundary confusion)
- Reflective or textureless surfaces
- Fine details (hair, fur, branches)
- Faces (specific issue: face segmentation can go wrong)

Lumen gave users tools to manually correct these depth errors. Phoenix provides the same tools.

**Important:** Depth edits do not change the depth map data file. They record corrections that are applied on top of the depth map during re-render. The depth corrections live in the `.lrp` sidecar.

---

## Accessing Depth Tools

1. Press `D` or click the "Depth" tab in the right panel
2. The depth overlay appears on the canvas automatically
3. The right panel shows the depth tool controls

---

## Depth Overlay

The depth map is visualized as a false-color overlay blended on top of the photo. The default blend mode is 40% opacity.

**False color map:**
- Near (closest): Warm red / orange
- Mid-distance: Yellow / green
- Far (furthest): Cool blue / purple

The overlay opacity is adjustable via a slider in the right panel (0% = no overlay, 100% = full overlay). Keyboard shortcut: `V` toggles overlay on/off.

**Overlay modes:**
- **Blend**: False color overlaid on the photo (default)
- **Isolated**: Shows depth map alone (no photo)
- **Edges**: Highlights rapid depth transitions (useful for finding problem edges)

---

## Depth Tool: Brush

**Purpose:** Paint a depth correction onto a region. Used when a contiguous area of the image has the wrong depth.

**How it works:**
1. Select the Brush tool (icon: paintbrush, keyboard: `B`)
2. Click and drag on the canvas to paint
3. The painted area is assigned a new depth value
4. The depth you're painting is determined by the Depth Picker (see below)

**Controls in right panel:**
| Control | Description |
|---------|-------------|
| Brush size | Circle radius in pixels at 100% zoom. Slider or `[` / `]` keys |
| Brush hardness | Feathering at edge. 100% = hard edge, 0% = fully feathered |
| Brush strength | How much the depth is shifted per stroke. 1–100% |
| Target depth | The depth value being painted (set via Depth Picker or click-to-sample) |
| Flow | Whether the brush applies continuously while held, or once per click |

**Target depth — Depth Picker:**
- A range slider showing the depth scale (near → far)
- The filled circle on the slider represents the depth being painted
- Alt+click on the canvas samples the depth at that pixel and sets it as the target
- The right panel shows the sampled depth value as a number (meters, if calibrated) or as a relative 0.0–1.0 value

**Cursor:** Circle at the current brush size, with a small number showing the current zoom-adjusted radius.

---

## Depth Tool: Lasso

**Purpose:** Select a region by drawing around it, then assign a single depth value to the entire selection. More precise than the brush for well-defined objects.

**How it works:**
1. Select the Lasso tool (icon: lasso, keyboard: `L`)
2. Click and drag to draw a freehand boundary around the region
3. Release to close the selection
4. The selection is highlighted as a marching ants outline
5. Use the Depth Picker in the right panel to set the depth for the selected region
6. Click Apply (or press Return) to commit
7. Press Escape to cancel

**Controls in right panel:**
| Control | Description |
|---------|-------------|
| Target depth | Depth Picker (same as brush) |
| Feather edge | Soft/hard edge blend (0px = hard, 0–50px feather) |
| Apply | Commits the depth change |
| Cancel | Discards selection |

**Multiple selections:** Each lasso operation creates a new edit in the undo stack. You cannot combine multiple lasso selections before applying — apply one, then do another.

---

## Depth Tool: Quick Select

**Purpose:** Automatically select a subject based on an initial user stroke. Like Photoshop's Quick Selection tool, but operating on depth discontinuities as well as color.

**How it works:**
1. Select Quick Select tool (icon: magic wand, keyboard: `Q`)
2. Paint roughly over the subject you want to select
3. The algorithm expands the selection to cover the full object, using depth and color edges
4. Adjust by painting more strokes (adds to selection) or Alt+painting (removes from selection)
5. Use the Depth Picker to assign depth to the selection
6. Click Apply or press Return

**Controls in right panel:**
| Control | Description |
|---------|-------------|
| Target depth | Depth Picker |
| + / – | Add to / subtract from selection (also: regular paint = add, Alt+paint = subtract) |
| Clear mask | Resets the selection without applying |
| Apply | Commits the depth change |

**Underlying API:** Maps to `CIAPI::DepthEditor::addQuickSelectStrokes()` + `pushQuickSelectDepthEdit()`.

---

## Depth Tool: Edge Heal

**Purpose:** Fix depth errors at object edges. Common problem: the depth map places a foreground object at background depth, or vice versa, at the boundary — causing fringing when blurred. Edge Heal re-traces the edge using color information.

**How it works:**
1. Select Edge Heal tool (icon: bandage/heal, keyboard: `H`)
2. Paint along an edge that has incorrect depth
3. The algorithm detects the actual color edge and aligns the depth transition to it
4. Automatically sharpens or softens the depth discontinuity as needed

**Controls in right panel:**
| Control | Description |
|---------|-------------|
| Brush size | Width of the heal zone on each side of the edge |
| Strength | 1–100% — how aggressively to realign |
| Edge type | Hard edge / Soft edge preference |

**Two variants (matching Lumen's DepthEditor API):**
- **Edge Heal**: For sharp foreground/background edges (`pushEdgeHealDepthEdit`)
- **Surface Heal**: For smooth depth surfaces that have noise (`pushSurfaceHealDepthEdit`)

Both use the same tool icon and controls — a toggle in the panel switches between the two variants.

---

## Depth Tool: Face Matting

**Purpose:** Toggle automatic face detection and matting. When enabled, the pipeline detects faces in the image and ensures they are assigned a consistent, correct depth — preventing the common problem of faces being split between near and far depth values, which causes unnatural bokeh on portraits.

**How it works:**
- A toggle switch in the right panel (not a drawing tool)
- When ON: pipeline re-renders with face matting active
- When OFF: pipeline uses raw depth without face matting

**Controls in right panel:**
- Toggle: **Face Matting** (on/off)
- No other controls — this is fully automatic

This feature is disabled when no face is detected in the image (the toggle grays out and shows "No faces detected").

---

## Depth Inspector

Available in all depth tool modes: a small floating panel (appears on canvas hover) shows:
- Depth value at cursor position (in relative units 0.0–1.0, or in meters if calibrated)
- Whether this pixel has been manually edited (shows a pencil icon if so)

Hold Alt to pin the inspector at the cursor position without moving.

---

## Reset Depth

A button at the bottom of the Depth panel: **"Reset Depth Edits"**

Removes all depth edits and reverts to the computed depth map. Requires confirmation dialog:

```
Reset depth edits for this photo?

This will remove all brush strokes, lasso selections,
and other depth corrections you have made.

The original depth map computed from the camera data
will be used.

This cannot be undone.

[Cancel]  [Reset Depth]
```

(Note: "Cannot be undone" is correct — it clears the entire edit stack for depth, not just one step. This is a deliberate divergence from undo behavior because clearing the full history is destructive in a way individual strokes are not.)

---

## Underlying Pipeline Contract

The depth tools require the pipeline to provide:

| What UI needs | Pipeline provides |
|--------------|-------------------|
| Depth map as a 2D float array | Per-pixel depth in relative units (0=near, 1=far) or metric (meters) |
| Re-render when depth edits change | `applyDepthEdits(edits) → trigger re-render` |
| Depth value at a pixel | `getDepthAtPoint(x, y) → float` |
| Face detection / matting | `enableFaceMatting(bool)` |
| Quick select segmentation | `addQuickSelectStrokes(strokes) → mask` |

The UI passes edit operations to the pipeline layer and receives updated renders back. The UI does not manipulate depth data directly.
