# 08 — Device Import (Camera Connection)

---

## Overview

The L16 connects to the desktop app to transfer photos. Lumen supported both USB and WiFi transfer. Lumen's binary contained `DeviceBrowser`, `VideosModel`, and `VideosModel::DownloadRequest` components — evidence of a video download capability in addition to photo transfer.

Phoenix v1 supports **USB only**. WiFi can be added later if the L16's WiFi transfer protocol is understood.

---

## Accessing the Device Panel

- Click the camera icon (🔌) in the toolbar
- Or: File > Connect Camera

The device panel opens as a right-side panel that replaces the edit controls. The Library view does not change.

---

## Connection States

### No Camera Connected

```
┌──────────────────────────────────────────────────────────────────────┐
│  CAMERA                                                      [×]    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│            [Camera illustration]                                     │
│                                                                      │
│            Connect your Light L16 via USB                           │
│            to import photos.                                         │
│                                                                      │
│            Make sure the camera is powered on.                       │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

The app polls for camera connection every 2 seconds when this panel is open. When a camera is detected, the panel transitions automatically.

---

### Camera Connected — Browse

```
┌──────────────────────────────────────────────────────────────────────┐
│  CAMERA: Light L16                                           [×]    │
│  Serial: L16-02532     Battery: 68%     Storage: 14.2 GB / 32 GB   │
├──────────────────────────────────────────────────────────────────────┤
│  [Select All]  [Import Selected (0)]  [Import All New (47)]         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                      │
│  │  ✓  │ │  ✓  │ │     │ │     │ │     │                      │
│  │ [img]│ │ [img]│ │ [img]│ │ [img]│ │ [img]│                      │
│  │      │ │      │ │      │ │      │ │      │                      │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘                      │
│  Already   Already   New     New      New                            │
│  imported  imported                                                  │
│                                                                      │
│  ┌──────┐ ┌──────┐ ┌──────┐                                         │
│  │     │ │     │ │     │                                         │
│  │ [img]│ │ [img]│ │ [img]│                                         │
│  │      │ │      │ │      │                                         │
│  └──────┘ └──────┘ └──────┘                                         │
│  New       New      New                                              │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│  Import destination: [~/Pictures/L16]  [Change…]                    │
└──────────────────────────────────────────────────────────────────────┘
```

**Photo grid shows:**
- Thumbnail from camera (the embedded preview in each LRI)
- "Already imported" badge (dimmed) for photos already in the library
- "New" label for photos not yet imported
- Checkbox in top-left for manual selection

**Import destination:** The folder where files will be copied. Default: `~/Pictures/L16/`. Within the destination, photos are organized by capture date into subfolders: `YYYY-MM-DD/`.

---

### Transfer in Progress

```
┌──────────────────────────────────────────────────────────────────────┐
│  CAMERA: Light L16                                           [×]    │
│  Importing 47 photos…                                                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  L16_05823.lri                                                       │
│  ██████████████████████░░░░░░░░░ 62%                                │
│  23.4 MB / 37.6 MB   Est. 8 seconds remaining                       │
│                                                                      │
│  17 of 47 photos transferred                                         │
│  ████████░░░░░░░░░░░░░░░░░░░░░░░ 36%                                │
│                                                                      │
│  [Cancel Import]                                                     │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

While transfer is in progress:
- The user can navigate to the Library view — the camera panel remains accessible
- Imported photos appear in the Library as they complete (the library updates live)
- Cancelling stops at the current photo boundary (does not leave a partial LRI)

---

### Transfer Complete

```
┌──────────────────────────────────────────────────────────────────────┐
│  Import Complete                                                     │
│                                                                      │
│  47 photos imported to                                               │
│  ~/Pictures/L16/2018-10-28/                                          │
│                                                                      │
│  [Show in Library]   [Import More]   [Done]                          │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

"Show in Library" switches to Library mode and filters to the newly imported folder. "Import More" returns to the browse state. "Done" closes the camera panel.

---

## Import Options

In Preferences > Import:

| Setting | Options |
|---------|---------|
| Import destination | Folder path (default: ~/Pictures/L16) |
| Organize by date | On/Off — creates YYYY-MM-DD subfolders (default: on) |
| After import | Do nothing / Open in Library / Eject camera |
| Delete from camera after import | Off by default, user can enable (with a confirmation on first use) |
| Auto-import when camera connects | Off by default |

---

## Library Integration

After import, the Library immediately shows the new photos. They appear in:
- The "All Photos" source
- The appropriate year group
- The "Last 30 Days" smart album
- The date subfolder if organized by date

Photos appear with "Unprocessed" status — the pipeline has not run yet. They show embedded LRI previews as thumbnails.

---

## v1 Scope Limitations

- **USB only** in v1. WiFi transfer protocol needs further research.
- **No video transfer** in v1. Lumen's `VideosModel::DownloadRequest` suggests it could download video clips. This is deferred.
- **No firmware update** via Phoenix in v1.
- **No camera settings** (exposure mode, WiFi config, etc.) in v1. The L16 has no USB control interface beyond file transfer.
