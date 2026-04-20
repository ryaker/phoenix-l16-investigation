# 03 — Library View

---

## Purpose

The Library view is where the user sees all their L16 captures, selects photos to edit, and organizes their collection. It is the starting point for every session.

It does not do any image processing. It shows thumbnails (generated from the preview data embedded in the LRI file, or from a cached render if available).

---

## Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  TOOLBAR                                                             │
│  [Import…]  [Library ●]  ────────────────  [🔍 Search]  [Sort ▼]  │
├──────────────┬──────────────────────────────────┬───────────────────┤
│ LEFT PANEL   │          THUMBNAIL GRID          │  RIGHT PANEL      │
│              │                                  │  (INFO)           │
│ Sources      │  ┌──────┐ ┌──────┐ ┌──────┐     │                   │
│              │  │      │ │      │ │      │     │  Filename         │
│ ▶ All Photos │  │ [img]│ │ [img]│ │ [img]│     │  L16_02532.lri    │
│   2018       │  │      │ │      │ │      │     │                   │
│   2019       │  └──────┘ └──────┘ └──────┘     │  Date             │
│   2020       │                                  │  2018-10-28       │
│   2021       │  ┌──────┐ ┌──────┐ ┌──────┐     │  18:43:22         │
│              │  │      │ │      │ │      │     │                   │
│ Smart Albums │  │ [img]│ │ [img]│ │ [img]│     │  Zoom             │
│              │  │      │ │      │ │      │     │  28mm             │
│ Unprocessed  │  └──────┘ └──────┘ └──────┘     │                   │
│ Edited       │                                  │  Cameras fired    │
│ Exported     │                                  │  10 of 16         │
│              │                                  │                   │
│              │                                  │  Exposure         │
│              │                                  │  1/250s  ISO 200  │
│              │                                  │                   │
│              │                                  │  Size             │
│              │                                  │  LRI: 142 MB      │
│              │                                  │                   │
│              │                                  │  Status           │
│              │                                  │  ○ Unprocessed    │
└──────────────┴──────────────────────────────────┴───────────────────┘
```

---

## Thumbnail Grid

### Thumbnail Size

Three sizes, switched by a segmented control in the toolbar:
- **Small**: ~120×90px tiles, 6-8 across
- **Medium**: ~200×150px tiles, 4-5 across (default)
- **Large**: ~320×240px tiles, 2-3 across

### Thumbnail Content

Each thumbnail shows:
- The image (from LRI embedded preview, or cached render)
- Bottom-left badge: zoom level icon (28mm / 70mm / 150mm indicator)
- Bottom-right badge: status indicator

**Status badges:**
| Icon | Meaning |
|------|---------|
| ○ (empty circle) | Never processed — only embedded preview available |
| ◐ (half circle) | Processed, no edits made |
| ● (filled circle) | Processed, edits saved |
| ↑ (arrow) | Export queued or in progress |
| ✓ (check) | Exported at least once |

### Loading Behavior

Thumbnails load in viewport order. Off-screen thumbnails are lazy-loaded as the user scrolls.

**Priority:**
1. Embedded preview from LRI (fast, low-res, always available) → shown immediately
2. Cached thumbnail (from previous render, stored in app cache) → replaces embedded preview if available
3. Fresh render (only triggered manually via right-click > "Generate Preview") → not automatic

Thumbnails never auto-trigger full pipeline processing. The user explicitly opens a photo to process it.

### Selection

- Click: select one photo, deselect others
- Shift+click: range select
- Cmd+click: toggle individual selection
- Cmd+A: select all
- Escape: deselect all

Multi-select only affects batch operations (batch export, batch delete from library).

### Interactions

| Action | Result |
|--------|--------|
| Double-click | Open in Editor mode |
| Right-click | Context menu (see below) |
| Press E | Open selected in Editor |
| Press Delete | Remove from library (with confirmation) |

**Right-click context menu:**
- Open in Editor
- Reveal in Finder
- Generate Preview (triggers a low-res render)
- Export…
- Remove from Library
- Get Info

---

## Left Panel — Sources

The sources list has two sections:

### Folders
- **All Photos**: shows every LRI in the library
- Year groups (e.g., "2018", "2019") — automatically generated from capture dates
- Individual folders (if the user has organized their LRIs into subfolders)
- User can add any folder via "+" at the bottom of the list
- Folders show a count of photos they contain

### Smart Albums (read-only, auto-generated)
- **Unprocessed**: LRIs that have never had a full render
- **Edited**: LRIs with a saved `.lrp` sidecar containing non-default settings
- **Exported**: LRIs that have been exported at least once
- **Today**: Imports from today
- **Last 30 Days**: Imports from the last month

The user cannot edit smart albums in v1.

---

## Right Panel — Info

When exactly one photo is selected, the info panel shows metadata extracted from the LRI file:

| Field | Source |
|-------|--------|
| Filename | Filesystem |
| Capture date/time | LRI protobuf header |
| Zoom level | LRI capture field |
| Cameras fired | LRI per-capture warp block (count of active modules) |
| Exposure time | LRI per-module exposure_ns |
| ISO | LRI per-module analog_gain → approximate ISO |
| File size | Filesystem |
| Sidecar | `.lrp` present / absent |
| Last exported | From `.lrp` export history |

When multiple photos are selected, the info panel shows:
- Count selected
- Total file size
- Date range (earliest to latest)

When nothing is selected, the info panel is empty.

---

## Toolbar Controls

### Search
Real-time text filter. Matches against:
- Filename
- Date (e.g., "2019-03" shows all March 2019 captures)
- Zoom level (e.g., "28mm", "70mm", "150mm")

### Sort
Dropdown with options:
- Date: Newest First (default)
- Date: Oldest First
- Filename: A→Z
- Filename: Z→A
- File Size: Largest First

### Thumbnail Size
Segmented control: S | M | L (Small / Medium / Large)

---

## Empty States

**Empty library (first launch):**
```
                [Camera icon]
        Your L16 photos will appear here.
        
        [Import Photos…]  [Connect Camera]
```

**Search returns no results:**
```
        No photos match "[query]"
        
        [Clear Search]
```

**Folder is empty:**
```
        No photos in this folder.
```

---

## Performance Notes

The thumbnail grid must scroll at 60fps even with 9,000+ photos. This requires:
- Virtualized scrolling (only DOM/render elements for visible thumbnails)
- Thumbnail images pre-decoded and cached at the display size
- No blocking operations on the main thread

The pipeline layer is never called from the Library view. Library is read-only with respect to the pipeline.
