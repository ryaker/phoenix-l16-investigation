# 02 — App Architecture: Screen Map and Window Layout

---

## Window Model

Lumen Phoenix is a **single-window application**. There is one primary window. Everything happens inside it. No floating palettes, no separate browser and editor windows.

This matches the Lightroom model, which Lumen clearly borrowed from: a single persistent window with a mode switcher in the toolbar.

### Primary Window Regions

```
┌─────────────────────────────────────────────────────────────────────┐
│  TOOLBAR (48px)                                                      │
│  [Logo] [Import] [Library | Editor]  ·····  [Export] [Device]       │
├──────────────┬──────────────────────────────────┬───────────────────┤
│              │                                  │                   │
│  LEFT        │                                  │  RIGHT            │
│  PANEL       │          CONTENT AREA            │  PANEL            │
│  (240px)     │          (fills remaining)       │  (280px)          │
│              │                                  │                   │
│              │                                  │                   │
│              │                                  │                   │
│              │                                  │                   │
│              │                                  │                   │
│              │                                  │                   │
├──────────────┴──────────────────────────────────┴───────────────────┤
│  STATUS BAR (24px)                                                   │
│  [Filename] [Dimensions] [Processing status] [Progress]             │
└─────────────────────────────────────────────────────────────────────┘
```

Panel widths are resizable. Panels can be collapsed with a toggle button (show/hide left panel, show/hide right panel). Keyboard shortcuts: `⌘[` = toggle left panel, `⌘]` = toggle right panel.

---

## App Modes

Two primary modes, switched by the toggle in the toolbar:

### Library Mode
- Content area shows a grid of photo thumbnails
- Left panel shows source list (folders, smart filters)
- Right panel shows metadata / info for selected photo
- Toolbar shows: Import button, search, sort, filter controls

### Editor Mode
- Content area shows the active photo at maximum size
- Left panel shows filmstrip (thumbnails of nearby photos in the same folder)
- Right panel shows editing controls (depth tools, refocus, tone, export)
- Toolbar shows: photo navigation arrows, zoom controls, undo/redo

Mode is remembered per session. App launches in Library mode if no photo was open at quit; in Editor mode at the last-edited photo if one was.

---

## Navigation Flow

```
                    ┌─────────────────────────────────────┐
                    │          LIBRARY MODE               │
                    │                                     │
                    │  Grid of all LRI thumbnails         │
                    │  Click to select                    │
                    │  Double-click → Editor Mode         │
                    └──────────────┬──────────────────────┘
                                   │ double-click or press E
                                   ▼
                    ┌─────────────────────────────────────┐
                    │          EDITOR MODE                │
                    │                                     │
                    │  Full-size photo view               │
                    │  Depth tools accessible             │
                    │  Refocus controls visible           │
                    │  Press G or Escape → Library Mode   │
                    └──────────────┬──────────────────────┘
                                   │ File > Export or Cmd+E
                                   ▼
                    ┌─────────────────────────────────────┐
                    │         EXPORT SHEET                │
                    │  (modal sheet, not full screen)     │
                    │  Format, quality, destination       │
                    │  Add to queue or export now         │
                    └─────────────────────────────────────┘
```

---

## Toolbar Detail

### Library Mode Toolbar

```
[⚡ Lumen Phoenix]  [↑ Import…]  [Library ● | Editor]  ──────────────  [🔍 Search]  [Sort ▼]  [🔌 Camera]
```

- **Import…**: Opens folder picker. Imports (copies) LRI files and associated metadata into the library.
- **Library | Editor**: Toggle switches, with Library filled/active.
- **Search**: Real-time filter by filename, date, capture metadata.
- **Sort**: Date (newest first), Date (oldest first), Filename, Focal length.
- **Camera**: Opens Device panel if camera is connected (USB or WiFi).

### Editor Mode Toolbar

```
[⚡ Lumen Phoenix]  [↑ Import…]  [Library | Editor ●]  [← →]  [🔍 ±]  [Fit | 1:1]  ─────  [↩ Undo]  [↪ Redo]  [↑ Export]
```

- **← →**: Previous / next photo in the current folder.
- **🔍 ±**: Zoom in / zoom out.
- **Fit | 1:1**: Zoom to fit window / zoom to 1:1 pixels.
- **Undo / Redo**: Applied to depth edits and tone adjustments. Cmd+Z / Cmd+Shift+Z.
- **Export**: Opens the export sheet for the current photo.

---

## Status Bar

Always visible. Shows:

- Filename of current photo (in Editor) or selection count (in Library)
- Image dimensions (e.g., "10432 × 7824 — 81.6 MP")
- Current activity: "Idle", "Processing preview…", "Rendering…", "Exporting 3 of 12…"
- Progress bar (only shown when processing or exporting, otherwise hidden)

---

## Keyboard Shortcuts (global)

| Key | Action |
|-----|--------|
| `G` | Switch to Library mode |
| `E` | Switch to Editor mode |
| `⌘[` | Toggle left panel |
| `⌘]` | Toggle right panel |
| `⌘Z` | Undo |
| `⌘⇧Z` | Redo |
| `Space` | Play/pause preview animation (in Refocus mode) |
| `F` | Toggle full-screen |
| `←` `→` | Previous / next photo (in Editor) |
| `⌘E` | Export current photo |
| `⌘I` | Import |
| `+` `-` | Zoom in / zoom out (in Editor) |
| `⌘0` | Zoom to fit |
| `⌘1` | Zoom 1:1 |
| `D` | Switch to depth edit mode (in Editor) |
| `R` | Switch to refocus mode (in Editor) |
| `T` | Switch to tone mode (in Editor) |
| `Escape` | Cancel current tool / exit full-screen |

---

## Window State Persistence

On quit, the app saves:
- Window size and position
- Whether left/right panels are shown
- Current mode (Library or Editor)
- Current photo (if in Editor)
- Library source (selected folder/filter)
- Sort/filter settings

On next launch, all of the above is restored.

---

## Multiple Monitors

The app runs in one window. It supports being dragged to a second monitor. There is no second-monitor-optimized view in v1.

---

## Menu Bar

Standard macOS menu bar. Key items beyond the defaults:

**File menu:**
- New Library… (Cmd+Shift+N)
- Open Library… (Cmd+O)
- Import… (Cmd+I)
- Export… (Cmd+E)
- Export All Selected… (Cmd+Shift+E)

**Edit menu:**
- Undo (Cmd+Z)
- Redo (Cmd+Shift+Z)
- Reset to Defaults (resets all edits for the current photo)

**View menu:**
- Library (G)
- Editor (E)
- Show/Hide Left Panel (Cmd+[)
- Show/Hide Right Panel (Cmd+])
- Show Depth Overlay (Cmd+D)
- Enter Full Screen (Cmd+Ctrl+F)

**Photo menu:**
- Go to Previous (Left arrow)
- Go to Next (Right arrow)
- Open in Finder
- Show .lrp Sidecar in Finder (developer/power user)

**Window menu:** Standard macOS.
