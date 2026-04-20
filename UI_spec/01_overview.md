# 01 — Overview, Goals, and Platform Decision

---

## What Lumen Was

Lumen was Light's official desktop app for processing L16 captures. It did three things:

1. **Transfer and organize** photos from the L16 camera to the desktop (via USB or WiFi)
2. **Process** raw LRI files into viewable high-resolution images using Light's proprietary computational photography pipeline
3. **Edit** the resulting images — specifically the depth map, the virtual depth-of-field, white balance, and basic tone adjustments — and export the result

Lumen ran on Windows and macOS. It was built on Qt 5.11 (2018). It does not run on Apple Silicon under Rosetta 2 — the Qt window system fails to initialize. The binary and the processing library (`libcp.dylib`) are Intel-only.

The processing pipeline is the hard part. The UI is not.

---

## What Lumen Phoenix Is

Lumen Phoenix is a modern macOS-first replacement for Lumen. It is a **desktop photo processing and editing application** for the Light L16 camera.

It uses a new implementation of the processing pipeline (built by the parallel agents working on LRI format, multi-view fusion, and ISP implementation). The UI spec in this folder describes the user experience that sits on top of that pipeline.

---

## Goals

**Primary:**
- Open LRI files and process them into viewable full-resolution images (81.6 MP fused output)
- Provide the same depth editing and virtual refocus capabilities that Lumen had
- Export processed images in JPEG, TIFF, DNG, and HDR formats
- Run natively on Apple Silicon

**Secondary:**
- Import photos from the L16 camera (USB and WiFi)
- Batch process multiple LRI files
- Provide a modern, fast, non-janky user experience

**Not in scope for v1:**
- Editing tools beyond what Lumen had (no curves, levels, etc. — those belong in Lightroom)
- Social sharing
- Cloud sync
- Video
- RAW export from individual camera modules (power user / developer feature, separate tool)

---

## Non-Goals

- This app does not try to compete with Lightroom or Capture One. It processes L16 captures to a high-quality output file that you then bring into your regular photo editor if you want further editing.
- No subscription, no cloud account required.
- No AI-based features that require a network connection.

---

## Platform Decision: Native macOS (SwiftUI)

**Rationale:**

The target user is a Light L16 owner who had Lumen installed on a Mac and can no longer run it. They are not on Windows (Windows users of Lumen would need a separate effort). The primary development machine for Phoenix is an Apple Silicon Mac.

SwiftUI provides:
- Native performance on Apple Silicon with no Rosetta overhead
- Metal-accelerated image display (critical for 81.6 MP images)
- macOS-native drag and drop, file system access, Quick Look
- No Electron / Chromium overhead
- Access to Core Image, Vision, Core ML for future features

The pipeline layer (Rust or Python with Metal compute, being built by other agents) will expose a clean API that the Swift UI layer calls. The UI is pure display and interaction — no image math happens in the UI layer.

**Future platforms:**
- iOS / iPadOS: same SwiftUI codebase can extend to a companion viewer / remote trigger app
- A separate Android capture app (with new firmware) is in scope for the broader project but is **not** part of this spec

---

## Design Philosophy

**Fast to a good result, not complete control.**

The L16 is a computational camera. The user does not control aperture, shutter, ISO — the camera does. What they control *post-capture* is equally unusual: they control focus point, virtual aperture (depth of field), and depth map corrections. These are not Lightroom-style sliders. They are spatial, interactive, painterly.

The UI should reflect this. The depth tools are primary, not secondary. The refocus interaction is the signature feature of the L16 — it should feel magical and responsive, not tucked into a panel.

**Principles:**
1. **One thing at a time.** The user is either browsing, editing, or exporting. These are distinct modes with distinct UIs.
2. **Non-destructive always.** The LRI file is never modified. All edits live in a sidecar.
3. **Fast feedback.** Preview renders at a reduced resolution while the user is editing. Full render only on demand or export.
4. **Depth is first-class.** Depth map visualization, depth editing tools, and virtual refocus are not buried in a sub-panel — they are visible and accessible from the main editing view.
5. **No mystery progress.** Processing is slow (81.6 MP is large). The user always knows what the app is doing.

---

## Sidecar Format: `.lrp` (Lumen Phoenix)

Every LRI file can have a companion `.lrp` file stored alongside it (same directory, same basename, `.lrp` extension). This file records:

- All depth edits made by the user
- White balance override (if any)
- Tone adjustments
- Crop/rotation
- Virtual aperture and focus distance settings
- Export history (what was exported, when, at what settings)

If no `.lrp` exists, the app processes the LRI with factory defaults. The `.lrp` is created on first edit and updated on every change (auto-save, no explicit save step required).

This replaces Lumen's `.lris` format. It is a new format designed for Phoenix — it does not need to be compatible with Lumen's `.lris` files.
