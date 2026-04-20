# 09 — Design System

---

## Design Philosophy

Photo editing apps need to get out of the way of the photo. The chrome should be as dark and neutral as possible. Bright UI elements next to a photo distort color perception — a bright white sidebar makes the photo look underexposed. Professional photo apps (Lightroom, Capture One, DaVinci Resolve) universally use dark themes for this reason.

Phoenix uses a **dark theme as the default, always on for the editing workspace**. System light/dark mode is respected in dialogs, preferences, and settings sheets — those are not color-sensitive contexts.

---

## Color Palette

### Base Colors

| Token | Value | Usage |
|-------|-------|-------|
| `bg-primary` | `#1A1A1A` | Main window background, canvas area |
| `bg-panel` | `#242424` | Left and right panels |
| `bg-elevated` | `#2E2E2E` | Toolbar, status bar |
| `bg-control` | `#383838` | Sliders, input fields, cards |
| `bg-hover` | `#404040` | Control hover state |
| `bg-selected` | `#4A4A4A` | Selected state background |

### Text Colors

| Token | Value | Usage |
|-------|-------|-------|
| `text-primary` | `#EBEBEB` | Body text, labels |
| `text-secondary` | `#999999` | Metadata, secondary labels |
| `text-disabled` | `#555555` | Disabled controls |
| `text-caption` | `#777777` | Captions, small hints |

### Accent Colors

| Token | Value | Usage |
|-------|-------|-------|
| `accent-blue` | `#3A8EFF` | Focus ring, active state, progress bars, links |
| `accent-orange` | `#FF7A2F` | Depth map near (warm end of false color) |
| `accent-cyan` | `#00C9E0` | Depth map far (cool end of false color) |
| `accent-green` | `#34C759` | Success states, "already imported" badge |
| `accent-red` | `#FF3B30` | Error states, warnings |
| `accent-yellow` | `#FFD60A` | Clipping indicators in histogram |

### Depth Map False Color Gradient

The depth overlay uses a perceptually uniform gradient:
- Closest (depth 0.0): `#FF4500` (red-orange)
- Near-mid (depth 0.3): `#FFD700` (yellow)
- Mid (depth 0.5): `#00E676` (green)
- Far-mid (depth 0.7): `#00B0FF` (light blue)
- Furthest (depth 1.0): `#7C4DFF` (purple)

---

## Typography

Phoenix uses the system font throughout (San Francisco on macOS). No custom typefaces.

| Role | Font | Size | Weight |
|------|------|------|--------|
| Toolbar labels | SF Pro | 13pt | Regular |
| Panel section headers | SF Pro | 11pt | Semibold |
| Control labels | SF Pro | 12pt | Regular |
| Input values | SF Pro Mono | 12pt | Regular |
| Metadata values | SF Pro | 11pt | Regular |
| Status bar | SF Pro | 11pt | Regular |
| Thumbnail captions | SF Pro | 10pt | Regular |

Numeric values (exposure, ISO, f-stop, dimensions) use SF Mono for alignment.

---

## Spacing

| Token | Value | Usage |
|-------|-------|-------|
| `space-xs` | 4px | Tight gaps, badge insets |
| `space-sm` | 8px | Control internal padding |
| `space-md` | 12px | Standard inter-control gap |
| `space-lg` | 16px | Section gaps |
| `space-xl` | 24px | Panel-level padding |

Panels use 16px horizontal padding and 12px vertical padding from edges to content.

---

## Components

### Sliders

All sliders use the same component:
- Track: 3px thick, `bg-control` color
- Filled portion: `accent-blue`
- Thumb: 14px circle, `#FFFFFF`, 1px border `bg-hover`
- Hover: thumb enlarges to 16px
- Drag: thumb enlarges to 18px

Sliders with a label and value:
```
White Balance
Kelvin ────────────●──────── 6500K
```
The label is left-aligned; the value is right-aligned on the same line.

### Toggle

Capsule toggle switch. ON state: `accent-blue` background. OFF state: `bg-control` background.

### Segmented Control

Used for mode switching (Refocus / Depth / Tone / Geometry), view mode (Library / Editor), and similar multi-choice selections.
- Active segment: `bg-selected` with `accent-blue` bottom border
- Inactive segments: `bg-elevated` background
- Height: 28px

### Buttons

**Primary button** (Export Now, Import, Apply):
- Background: `accent-blue`
- Text: `#FFFFFF`, 13pt medium
- Corner radius: 6px
- Padding: 8px vertical, 16px horizontal

**Secondary button** (Cancel, Add to Queue):
- Background: `bg-control`
- Text: `text-primary`
- Border: 1px `bg-hover`
- Same size as primary

**Destructive button** (Reset, Delete):
- Same shape as primary but background `accent-red`

**Ghost button** (small inline actions):
- No background
- Text: `accent-blue`
- No border
- Used for "Change…", "Browse…", inline links

### Input Fields

- Background: `bg-control`
- Text: `text-primary`, SF Mono for numbers
- Border: 1px `bg-hover`, 2px `accent-blue` on focus
- Corner radius: 4px
- Height: 28px

### Cards (for thumbnail captions, queue items)

- Background: `bg-panel`
- Corner radius: 6px
- 1px border: `bg-hover`

---

## Icons

Use SF Symbols (macOS system icon set) throughout. This ensures consistent sizing, weight, and dark mode compatibility with zero custom asset work.

Key icons:

| Usage | SF Symbol |
|-------|-----------|
| Import | `square.and.arrow.down` |
| Export | `square.and.arrow.up` |
| Camera | `camera` |
| Library mode | `photo.on.rectangle` |
| Editor mode | `slider.horizontal.3` |
| Depth tool | `mountain.2` |
| Refocus | `dot.circle` |
| Tone | `sun.max` |
| Brush | `pencil.tip` |
| Lasso | `lasso` |
| Quick select | `wand.and.rays` |
| Heal | `bandage` |
| Face matting | `person.crop.circle` |
| Undo | `arrow.uturn.backward` |
| Redo | `arrow.uturn.forward` |
| Zoom in | `plus.magnifyingglass` |
| Zoom out | `minus.magnifyingglass` |
| Full screen | `arrow.up.left.and.arrow.down.right` |
| Settings | `gear` |
| Close | `xmark` |

Custom icons (only if SF Symbols does not have a good match):
- L16 camera silhouette (for empty device panel)
- Depth false-color gradient icon (for the depth overlay toggle)

---

## Motion and Animation

Keep animation minimal. Photo editors are tools, not entertainment apps.

| Interaction | Animation |
|-------------|-----------|
| Mode switch (Library ↔ Editor) | Cross-dissolve, 200ms |
| Panel show/hide | Slide + fade, 200ms |
| Sheet (Export, etc.) | Slide down from top, 250ms |
| Focus ring on canvas | Expand + fade, 400ms |
| Thumbnail hover | Scale to 1.02×, 100ms |
| Progress bar | Linear fill, no spring |
| Loading spinner | Standard macOS spinner |

No bouncy springs. No parallax. No easing curves that slow things down.

---

## Accessibility

- All controls have accessibility labels
- Slider values announced by VoiceOver with units ("f/4.0", "6500 Kelvin")
- Keyboard navigation covers all primary features
- Minimum touch target size: 44×44 points (matches Apple HIG)
- Color is never the sole indicator of state (badges use both color and icon)
- Reduce Motion: all animations disabled, instant transitions

---

## Canvas Rendering Requirements

The canvas renders an 81.6 MP image at interactive frame rates. This requires:

- Metal-backed view (`MTKView`)
- Image delivered as a Metal texture from the pipeline layer
- Zoom and pan with GPU-side transform (no CPU readback)
- Depth overlay composited on GPU as a second texture + blend shader
- Brush cursor rendered with CALayer or Metal overlay (not AppKit cursor — cursor is too small at 100% zoom)

The canvas is not a standard `NSImageView`. It is a custom `MTKView` subclass.
