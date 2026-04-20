# 07 — Export

---

## Export Concept

Export is how processed photos leave the app. There are two export paths:

1. **Single export**: Export the current photo now, with a file picker
2. **Export queue**: Add one or more photos to a background queue, configure each, let the queue process them while you keep working

Both paths share the same settings sheet.

---

## Triggering Export

- **Cmd+E**: Opens export sheet for the current photo
- **Toolbar "Export" button**: Same as Cmd+E
- **File > Export**: Same
- **File > Export All Selected…**: Opens export sheet, with the selection batch pre-loaded
- **Right-click in Library > Export…**: Export the right-clicked photo

---

## Export Sheet

A modal sheet that slides down from the top of the window.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Export: L16_02532.lri                                               │
├──────────────────────────────────────┬──────────────────────────────┤
│  PREVIEW (small thumbnail)           │  OUTPUT SETTINGS             │
│                                      │                              │
│  [photo thumbnail]                   │  Format                      │
│                                      │  ● JPEG    ○ TIFF            │
│  Approx output size: 48 MB           │  ○ DNG     ○ HDR (EXR/HDR)  │
│                                      │                              │
│                                      │  ── JPEG settings ──         │
│                                      │  Quality: ────────●── 92    │
│                                      │  [ ] Include depth map (XMP) │
│                                      │                              │
│                                      │  Color Space                 │
│                                      │  [sRGB ▼]                    │
│                                      │  (sRGB, Display P3, AdobeRGB)│
│                                      │                              │
│                                      │  Size                        │
│                                      │  ● Original (10432 × 7824)   │
│                                      │  ○ Long edge: [──4000──]     │
│                                      │  ○ Short edge: [──3000──]    │
│                                      │  ○ Custom: [W: 4160] [H: 3120]│
│                                      │                              │
│                                      │  Metadata                    │
│                                      │  [x] Include capture metadata│
│                                      │  [ ] Include GPS (none avail)│
│                                      │                              │
├──────────────────────────────────────┴──────────────────────────────┤
│  Destination                                                         │
│  [/Users/ryaker/Pictures/L16 Exports]  [Change…]                    │
│                                                                      │
│  Filename: [L16_02532] . [jpg]         [Add suffix: _edit _full]    │
├──────────────────────────────────────────────────────────────────────┤
│                              [Cancel]  [Add to Queue]  [Export Now]  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Output Formats

### JPEG
- Quality slider: 1–100 (default 92)
- Option: Include depth map as XMP sidecar (`.xmp` written alongside the JPEG) or embedded in the JPEG's XMP metadata
- Produces: Standard JPEG, sRGB or P3 gamut, 8-bit
- Best for: Sharing, web, general use

### TIFF
- Bit depth: 8-bit or 16-bit
- Compression: None / LZW / ZIP
- Produces: Large file (~150-300 MB at 16-bit) but lossless
- Best for: Bringing into Lightroom, Photoshop, or other post-processing

### DNG
- Adobe DNG format with embedded depth map (Google Depth Map XMP format, same as Lumen's DNG export)
- Bit depth: 16-bit
- Option: Include sidecar `.lrp` embedded in DNG metadata
- Produces: Opens in Lightroom, Photoshop, Preview, macOS
- Best for: Maximum flexibility, archival, editing in another app

### HDR (EXR or Radiance HDR)
- Format: OpenEXR (preferred) or Radiance `.hdr`
- 32-bit float per channel
- No tone mapping applied — linear scene-referred data
- Best for: AI pipeline input, computational post-processing, scientific use

---

## Color Space

Dropdown options:
- **sRGB**: Standard, widest compatibility (default for JPEG/DNG)
- **Display P3**: Apple wide gamut, best for Apple devices (default for TIFF)
- **Adobe RGB (1998)**: Print workflows
- **Linear sRGB**: No gamma, for HDR/EXR export (disabled for JPEG)

---

## Size Options

- **Original**: Always 10432 × 7824 for the L16 (81.6 MP)
- **Long edge**: Constrain the longest dimension; aspect ratio preserved
- **Short edge**: Constrain the shortest dimension; aspect ratio preserved
- **Custom**: Enter exact width and height; shows warning if aspect ratio differs from original

---

## Filename

- Default: original LRI filename without extension
- Suffix presets: `_edit`, `_full`, `_portrait`, `_sharp` — one-click to append
- Custom suffix: type anything in the suffix field
- Final filename shown as preview: e.g., `L16_02532_portrait.jpg`
- If file already exists at destination: options are "Replace" or "Add number" (_1, _2, etc.) — set in Preferences, not per-export

---

## Export Now vs. Add to Queue

**Export Now:**
- Begins export immediately
- Sheet closes when export starts
- A non-modal progress indicator appears in the status bar
- User can keep working
- A notification (macOS notification) appears when export completes

**Add to Queue:**
- Adds the export job to the export queue (see below)
- Sheet closes
- User can add more jobs from other photos
- Queue processes jobs in the background, one at a time (to avoid overwhelming the system)

---

## Export Queue

A non-modal panel that shows the current and pending export jobs.

**Access:** Click the "Exports" indicator in the status bar (only visible when queue has items), or View > Show Export Queue.

```
┌──────────────────────────────────────────┐
│  Export Queue                        [×] │
├──────────────────────────────────────────┤
│  ▶ L16_02532_portrait.jpg    ████████░░  │
│    Exporting… 72%            [Cancel]    │
├──────────────────────────────────────────┤
│  ○ L16_04574_sharp.tiff      Waiting     │
│    [Remove]                              │
│                                          │
│  ○ L16_00177_full.jpg        Waiting     │
│    [Remove]                              │
├──────────────────────────────────────────┤
│  [Pause Queue]              3 jobs total │
└──────────────────────────────────────────┘
```

- Active job shows progress bar
- Waiting jobs show "Waiting" and a Remove button
- Completed jobs show a check mark for 3 seconds then disappear
- Failed jobs show a red ✕ and "Failed: [reason]" — clicking opens a dialog with the error

**Pause Queue:** Suspends processing after the current job finishes. Resumes from where it left off.

---

## Export History

After successful export, the `.lrp` sidecar records:
- Export date/time
- Export format and settings
- Output path

This is surfaced in the Library info panel as "Last exported: Apr 10, 2026 as JPEG".

---

## Batch Export from Library

1. Select multiple photos in Library view (Cmd+click or Shift+click)
2. Cmd+Shift+E or File > Export All Selected…
3. The same export sheet opens, but the header shows "Export 12 photos"
4. All settings apply to all selected photos
5. "Add to Queue" or "Export Now" processes all selected photos with those settings
6. Each photo gets its own job in the export queue

---

## Preferences: Export Defaults

In Preferences > Export:
- Default format (JPEG)
- Default JPEG quality (92)
- Default color space (sRGB)
- Default destination folder
- Filename collision behavior (Replace / Add number / Ask)
- After export: Open in Finder? Open file? Do nothing?
