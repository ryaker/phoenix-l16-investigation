# Lumen Phoenix — UI/UX Specification

**Status:** Draft v1  
**Author:** UI spec agent  
**Date:** 2026-04-11  
**Source material:** Lumen.app binary analysis, libcp.dylib API, L16 tech docs, lumen-phoenix-investigation.md

---

## What This Is

A complete product specification for the modern desktop app that replaces Lumen.app.

This spec covers:
- What screens exist and what they do
- How users navigate between them
- What controls appear in each context and how they behave
- What the pipeline layer must provide for each screen to work
- Design language and platform decisions

This spec does **not** cover:
- How the pipeline computes images (other agents own that)
- Internal data structures or file formats
- Build tooling or CI/CD

---

## Document Index

| File | Contents |
|------|----------|
| `README.md` | This file — orientation and index |
| `01_overview.md` | Goals, non-goals, platform decision, design philosophy |
| `02_app_architecture.md` | Screen map, navigation model, window layout |
| `03_library_view.md` | Photo browser — the entry point |
| `04_editor_view.md` | Main editing workspace |
| `05_depth_tools.md` | Depth map visualization and depth editing tools |
| `06_refocus_dof.md` | Virtual refocus / depth-of-field controls |
| `07_export.md` | Export dialog and batch export queue |
| `08_device_import.md` | Camera connection, transfer, import |
| `09_design_system.md` | Colors, typography, spacing, iconography |
| `04b_tone_geometry.md` | Tone adjustments (WB, exposure, etc.) and Geometry (crop, rotate, flip) |
| `10_pipeline_api_contract.md` | What the UI needs from the processing pipeline |

---

## Key Decisions (summary — details in each file)

- **Platform:** Native macOS (SwiftUI) first. iOS later. Not cross-platform Electron.
- **Architecture:** Single window, three-panel layout. Library ↔ Editor are modes, not separate windows.
- **State format:** Every edit is non-destructive. Original LRI never modified. Sidecar file (`.lrp` — Lumen Phoenix) stores all edits.
- **Depth editing:** Lumen had full depth editing tools (brush, lasso, quick-select, face matting, heal). Phoenix keeps all of them.
- **Refocus:** Virtual aperture slider + click-to-focus are the signature L16 feature. These are prominent, not buried.
- **Export:** Non-blocking background queue. Formats: JPEG, TIFF, DNG, HDR.
- **No cloud dependency.** All processing is local.
