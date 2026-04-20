# 10 — Pipeline API Contract

---

## Purpose

This document defines what the UI layer needs from the processing pipeline, expressed as a clean interface contract. The pipeline agents implement this. The UI agents implement against it.

The pipeline is a black box from the UI's perspective. It takes LRI files and parameters, returns images and metadata. The UI never touches pixel data directly.

---

## Architecture Boundary

```
┌─────────────────────────────────────────────────────────────┐
│                    SwiftUI Layer                             │
│  Views, controls, interactions, layout, animation           │
└────────────────────────────┬────────────────────────────────┘
                             │  calls
┌────────────────────────────▼────────────────────────────────┐
│                  Pipeline API (Swift)                        │
│  Protocol definitions, async/await interfaces               │
│  Bridges to the Rust/Python processing layer                │
└────────────────────────────┬────────────────────────────────┘
                             │  calls
┌────────────────────────────▼────────────────────────────────┐
│           Processing Layer (Rust / Python + Metal)          │
│  Multi-camera ISP, depth estimation, fusion, tone mapping   │
│  Depth editing operations, bokeh synthesis                  │
└─────────────────────────────────────────────────────────────┘
```

The Swift Pipeline API layer is the contract boundary. Everything above the line is UI. Everything below the line is pipeline. They are developed independently.

---

## Core Types

```swift
/// A reference to a single LRI capture file. Opaque to the UI.
struct LRICapture {
    let path: URL
    let captureID: String  // derived from filename, e.g. "L16_02532"
}

/// Capture metadata extracted from the LRI header (no image processing required).
struct CaptureMetadata {
    let captureDate: Date
    let zoomLevelMM: Int           // 28, 70, or 150
    let activeCameraCount: Int     // typically 10–14
    let exposureSeconds: Double    // representative exposure (first A-camera)
    let approximateISO: Int        // derived from analog gain
    let fileSize: Int64            // bytes
    let hasSidecar: Bool           // .lrp file exists
}

/// Current edit state for a capture. Persisted in the .lrp sidecar.
struct EditState {
    var whiteBalance: WhiteBalanceParams
    var toneAdjustments: ToneParams
    var cropRotation: CropParams
    var depthEdits: [DepthEdit]
    var focusDistance: Float       // 0.0=nearest, 1.0=furthest, or in meters
    var virtualAperture: Float     // f-number, e.g. 4.0
    var bokehShape: BokehShape
    var tiltFocusEnabled: Bool
    var tiltFocusPlane: FocusPlane?
    var faceMattingEnabled: Bool
}

/// Represents a single depth edit operation.
enum DepthEdit {
    case brush(BrushDepthEdit)
    case lasso(LassoDepthEdit)
    case quickSelect(QuickSelectEdit)
    case edgeHeal(HealEdit)
    case surfaceHeal(HealEdit)
}

/// The result of a render operation.
struct RenderResult {
    let texture: MTLTexture        // Metal texture — use directly in MTKView
    let depthTexture: MTLTexture?  // Depth map as a normalized float texture
    let width: Int
    let height: Int
    let renderLevel: RenderLevel
}

enum RenderLevel {
    case thumbnail     // ~512px long edge, from embedded LRI preview
    case preview       // ~2048px long edge, fast pipeline render
    case full          // 10432×7824, full pipeline render
}
```

---

## LRI Library Operations

```swift
protocol LRILibraryProtocol {
    /// Extract metadata from an LRI file without running the processing pipeline.
    /// Fast — reads only the LRI header. Called for every file in the library.
    func metadata(for capture: LRICapture) async throws -> CaptureMetadata

    /// Return the embedded preview image from the LRI file.
    /// Fast — no processing. Used for thumbnails before any render.
    func embeddedPreview(for capture: LRICapture) async throws -> MTLTexture
}
```

---

## Rendering Operations

```swift
protocol LRIRendererProtocol {
    /// Render at the specified quality level.
    /// Returns a stream of results as rendering progresses (thumbnail → preview → full).
    func render(
        capture: LRICapture,
        editState: EditState,
        targetLevel: RenderLevel
    ) -> AsyncThrowingStream<RenderResult, Error>

    /// Cancel an in-progress render.
    func cancel(capture: LRICapture)

    /// Re-render with updated edit state (e.g., aperture changed).
    /// Implicitly cancels any in-progress render for this capture.
    func rerender(capture: LRICapture, editState: EditState, targetLevel: RenderLevel) -> AsyncThrowingStream<RenderResult, Error>

    /// Check if a render is cached at the given level.
    func isCached(capture: LRICapture, editState: EditState, level: RenderLevel) -> Bool
}
```

---

## Depth Operations

```swift
protocol DepthProtocol {
    /// Get the depth value at a pixel (normalized 0.0=near, 1.0=far).
    /// Returns nil if depth map not yet computed.
    func depthAtPoint(_ point: CGPoint, capture: LRICapture) async -> Float?

    /// Compute a quick-select mask from initial brush strokes.
    /// Returns a mask texture (white=selected, black=unselected).
    func computeQuickSelectMask(
        strokes: [QuickSelectStroke],
        capture: LRICapture
    ) async throws -> MTLTexture

    /// Apply a depth edit to the edit state. Does not re-render.
    /// Re-render is triggered separately after all desired edits are applied.
    func applyDepthEdit(_ edit: DepthEdit, to editState: inout EditState)

    /// Detect faces in the rendered image.
    /// Returns bounding rects in image coordinates.
    func detectFaces(in render: RenderResult) async -> [CGRect]
}
```

---

## Refocus Operations

```swift
protocol RefocusProtocol {
    /// Get the depth at a point (same as depth protocol, aliased for clarity).
    func focusDistanceAtPoint(_ point: CGPoint, capture: LRICapture) async -> Float?

    /// Validate that the given focus distance and aperture combination
    /// will produce a meaningful result (e.g., not entirely OOF).
    /// Returns a suggestion if the combination is degenerate.
    func validateRefocusParams(
        focusDistance: Float,
        aperture: Float,
        capture: LRICapture
    ) -> RefocusValidation
}

struct RefocusValidation {
    let isValid: Bool
    let warning: String?  // e.g., "Subject may be out of focus at this aperture"
}
```

---

## Export Operations

```swift
protocol ExportProtocol {
    /// Export a capture to a file with the given settings.
    /// Progress is reported via the AsyncThrowingStream (0.0–1.0).
    func export(
        capture: LRICapture,
        editState: EditState,
        settings: ExportSettings,
        destination: URL
    ) -> AsyncThrowingStream<Double, Error>

    /// Cancel an in-progress export.
    func cancelExport(capture: LRICapture)
}

struct ExportSettings {
    var format: ExportFormat        // jpeg, tiff, dng, hdr
    var quality: Double             // 0.0–1.0 for JPEG; ignored for lossless
    var colorSpace: ColorSpace      // sRGB, p3, adobeRGB, linear
    var bitDepth: Int               // 8 or 16
    var outputSize: OutputSize      // original, longEdge(px), shortEdge(px), custom(w,h)
    var includeDepthMap: Bool       // embed depth in XMP (JPEG/DNG)
    var includeMetadata: Bool       // include EXIF / capture metadata
}

enum ExportFormat { case jpeg, tiff, dng, hdr }
enum ColorSpace { case sRGB, displayP3, adobeRGB, linearSRGB }
enum OutputSize {
    case original
    case longEdge(Int)
    case shortEdge(Int)
    case custom(width: Int, height: Int)
}
```

---

## Tone Adjustments

These map to pipeline parameters for the post-fusion tone mapping stage.

```swift
struct ToneParams {
    var exposureEV: Float           // -3.0 to +3.0, default 0.0
    var highlights: Float           // -100 to +100, default 0.0
    var shadows: Float              // -100 to +100, default 0.0
    var whites: Float               // -100 to +100, default 0.0
    var blacks: Float               // -100 to +100, default 0.0
    var contrast: Float             // -100 to +100, default 0.0
    var clarity: Float              // -100 to +100, default 0.0
    var vibrance: Float             // -100 to +100, default 0.0
    var saturation: Float           // -100 to +100, default 0.0
}

struct WhiteBalanceParams {
    var temperature: Int            // 2000–12000 Kelvin, default from LRI capture
    var tint: Int                   // -150 to +150 (Magenta–Green), default 0
    var useCaptureWB: Bool          // if true, use factory AWB from LRI header
}
```

---

## Geometry / Crop

```swift
struct CropParams {
    var cropRect: CGRect?           // nil = no crop (full image)
    var rotationDegrees: Float      // -45 to +45, default 0.0
    var flipHorizontal: Bool
    var flipVertical: Bool
}
```

---

## Error Handling

The pipeline layer throws typed errors. The UI maps them to user-visible messages.

```swift
enum PipelineError: Error {
    case fileNotFound(URL)
    case corruptedLRI(URL, String)       // message from pipeline
    case unsupportedFirmwareVersion(Int)
    case renderFailed(String)
    case exportFailed(String)
    case insufficientMemory(requiredGB: Double)
    case depthNotAvailable               // depth map could not be computed
    case cancelled                        // user cancelled
}
```

---

## Performance Expectations

The UI relies on these performance characteristics to deliver a good user experience.

| Operation | Target latency | Notes |
|-----------|---------------|-------|
| `metadata(for:)` | < 50ms | Reads only LRI header, no processing |
| `embeddedPreview(for:)` | < 100ms | Reads embedded preview from LRI |
| Render to `.preview` level | < 5s | On M1 or later; pipeline implements fast path |
| Render to `.full` level | < 60s | On M1 or later; 81.6 MP fused image |
| Re-render with new aperture | < 5s (preview) | Bokeh synthesis on already-rendered base image |
| Re-render with new focus point | < 2s (preview) | Focus point change is cheap |
| `depthAtPoint(_:)` | < 10ms | Synchronous depth lookup |
| `export(...)` at full res | < 120s | JPEG at quality 92 to disk |
| `computeQuickSelectMask` | < 2s | Segmentation from strokes |

The UI makes no assumptions about pipeline internals. If performance doesn't meet these targets, the UI degrades gracefully (spinner, progress bar, "still rendering…" message) — it does not break.

---

## Threading Model

- All pipeline operations are `async` — they run off the main thread
- Render results (Metal textures) are delivered to the UI on the main actor
- Progress callbacks are delivered on the main actor
- The UI never blocks the main thread waiting for pipeline work

The pipeline layer is responsible for managing its own thread pool, GPU command queues, and memory.
