# Lumen.app — C++ Library Inventory for Linking & Reverse Engineering

**Source bundle:** `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app`
**Generated:** 2026-04-10
**Scope:** Catalog every native C++ library shipped inside the Lumen.app bundle, classify by reuse value, and document what's callable vs. what's only reachable through reverse engineering.

---

## TL;DR

Lumen.app ships three Light-proprietary C++ libraries and one bundled dependency (Ceres) that are interesting for reuse. Everything else in the bundle is stock Qt 5.11.1 or Qt plugins and is not worth reverse engineering.

| Library | Size | Arch | What it is | Reuse verdict |
|---|---|---|---|---|
| **libcp.dylib** | 6.93 MB | x86_64 only | Light's core image pipeline (CIAPI + internal `lt::` namespace, Halide-compiled kernels) | **PRIMARY TARGET** — link or RE |
| **liblricompression.dylib** | 2.77 MB | x86_64 only | Light's LRI container reader/writer (`ltCompress::CompressLRI`) | **HIGH VALUE** — link or RE |
| **libceres.dylib** | 2.49 MB | x86_64 only | Google Ceres Solver (bundled, not Light code) | Replace with upstream — no RE needed |
| Sparkle.framework | — | — | Autoupdater, irrelevant to pipeline | Ignore |
| Qt 5.11.1 frameworks + plugins | — | x86_64 | Stock Qt, open source | Ignore for RE; replace with upstream Qt or drop entirely |

**The Apple Silicon problem:** Every Light-proprietary dylib is x86_64-only, compiled against Qt 5.11.1 (released 2018) with Clang 8.1.0 from `libhalide` nightly build slaves. That's why Lumen.app ran under Rosetta but couldn't open a window — Qt 5.11.1's macOS backend has known incompatibilities with modern Apple Silicon. The Light C++ code itself (libcp, liblricompression) is architecture-independent; only the build target is stale.

---

## Tier 1 — Light Proprietary (High Reverse-Engineering Value)

### 1. libcp.dylib — Core Image Pipeline

```
Path:     Contents/Frameworks/libcp.dylib
Size:     6,935,696 bytes (6.93 MB)
Arch:     Mach-O 64-bit x86_64
Exports:  411 public symbols
Links:    libceres.dylib, libSystem, libc++
```

**This is the crown jewel.** Every symbol you care about for L16 fusion, depth editing, color science, and DNG writing lives in here.

#### Top-level exported namespaces (C++ public API)

Light's public wrapper namespace is `CIAPI::` (C Image API):

```
CIAPI::GetVersion()
CIAPI::ApplyTuning
CIAPI::BrushDepthEditingParams       CIAPI::LassoDepthEditingParams
CIAPI::CreateMemStream                CIAPI::CreateMultiStream
CIAPI::DepthEditor                    CIAPI::DirectRenderer
CIAPI::ExportImageFormat              CIAPI::HealDepthEditingParams
CIAPI::Image                          CIAPI::ImagePyramid
CIAPI::ParamByteArray | ParamFloat | ParamFloatArray | ParamInt | ParamIntArray | ParamString
CIAPI::Point                          CIAPI::PropertyAccessor
CIAPI::QuickSelectDepthEditingParams  CIAPI::RectF
CIAPI::Renderer                       CIAPI::RendererBase
CIAPI::RendererProfile                CIAPI::RenderingMode
CIAPI::RenderType                     CIAPI::ResetMode
CIAPI::ROI                            CIAPI::StateChange
CIAPI::StateFileEditor                CIAPI::StateType
CIAPI::StaticShutdown                 CIAPI::Transform
CIAPI::TuningType
```

#### `CIAPI::Renderer` — the entry point you actually want

Every method you'd need to drive LRI → rendered image from external code is exported here:

```cpp
Renderer::Renderer()
Renderer::Renderer(std::shared_ptr<lt::RendererPrivate> const&)
Renderer::~Renderer()

// Lifecycle
Renderer::IsHardwareCompatible()
Renderer::abort()
Renderer::cancelRenderRequests()
Renderer::setMode(CIAPI::RenderingMode)
Renderer::setProgressUpdateListener(std::function<void(int)>)
Renderer::setOutputUpdateListener(std::function<void(ImagePyramid const&, ROI const&, int)>)
Renderer::setStateChangeListener(std::function<void(StateChange, void*)>)
Renderer::implementation()        // leaks pimpl — potential deep entry

// Render + output
Renderer::render(int, ROI const&, RenderType, bool)
Renderer::outputBuffer() const
Renderer::writeImage(std::shared_ptr<ostream> const&,
                     Point<int> const&,
                     ExportImageFormat,
                     std::function<void(int)>)

// State persistence
Renderer::serialize(std::shared_ptr<ostream> const&, StateType)
Renderer::deserialize(std::shared_ptr<istream> const&, StateType)
```

**This `writeImage()` call is the real DNG writer** your memory `project_lri_process_cli.md` flagged as the correct path. The standalone `lri_process` CLI bypasses it and writes JPEGs with `.dng` extensions; calling `Renderer::writeImage` directly with `ExportImageFormat::DNG` is how you get ground-truth DNGs without the Lumen GUI.

#### `CIAPI::DepthEditor` — full exported surface

```cpp
DepthEditor::DepthEditor(Renderer&)
DepthEditor::reset()
DepthEditor::redoDepthEdit() / undoDepthEdit()
DepthEditor::getDepthAtPoint(Point<float> const&)
DepthEditor::pushBrushDepthEdit(BrushDepthEditingParams const&)
DepthEditor::pushLassoDepthEdit(LassoDepthEditingParams const&)
DepthEditor::pushEdgeHealDepthEdit(HealDepthEditingParams const&)
DepthEditor::pushSurfaceHealDepthEdit(HealDepthEditingParams const&)
DepthEditor::pushQuickSelectDepthEdit(float)
DepthEditor::addQuickSelectStrokes(QuickSelectDepthEditingParams const&)
DepthEditor::clearQuickSelectMask()
DepthEditor::quickSelectMask()
DepthEditor::resetQuickSelect()
DepthEditor::enableFaceMatting(bool)
```

Every depth-edit operation the Lumen UI exposes is publicly callable. If you want to reproduce Lumen's "ground truth" depth editing from Python or Rust, binding these is straightforward.

#### Internal namespaces visible in exports (reverse-engineering targets)

```
CacheEntry::        DirectRenderer::      Halide::
Image::             ImagePyramid::        Internal::
PropertyAccessor::  Renderer::            RendererBase::
Runtime::           StateFileEditor::     Transform::
```

And, critically, the **`lt::` internal namespace** surfaces in embedded strings with the fusion pipeline:

```
lt::ColorFusionBayer
lt::FusionCacheBayer
lt::Internal::BayerPipelinePayload
lt::Internal::BayerFloatPipelinePayload
lt::Internal::PackBayerImageProtoType<vec4x16ui, ushort>
```

**This is the L16 fusion pipeline you're trying to rebuild.** `ColorFusionBayer` and `FusionCacheBayer` are the type names that directly correspond to per-module Bayer fusion — the thing your `L16_PIPELINE_SPEC.md` says is missing from the current reimplementation. These are not in the CIAPI public namespace and are mangled into C++ with templates, so they require static RE (Ghidra / IDA / binja), not direct linking.

#### Halide DSL embedded inside libcp

```
halide_runtime
halide_set_num_threads
.../halide/src/runtime/profiler.cpp:204
.../halide/src/runtime/tracing.cpp:41
```

libcp was built by **AOT-compiling Halide kernels into the dylib**. That means the image processing stages (demosaic, denoise, color fusion, tonemap) exist as generated machine code inside libcp, not as portable Halide IR. You can't just "extract the Halide source" — it was compiled from a private source tree. What you *can* do:

1. Identify Halide-generated functions by symbol prefix (`_ZN...Halide...`) and signature (buffer-passing convention with `halide_buffer_t*`).
2. For each kernel, reverse-engineer its purpose from strings and call sites.
3. Re-implement in modern Halide (or plain Rust/SIMD) if you want to ship a non-Lumen binary.

#### DNG writer confirmation

```
DNGWriter: Tile Index overrun
```

String evidence that a proper `DNGWriter` class exists inside libcp, confirmed by your memory note. It's routed through `CIAPI::Renderer::writeImage(..., ExportImageFormat::DNG, ...)` — the direct link target.

#### Bayer pipeline strings (internal topology hints)

```
Bayer image must have even dimensions!
BAYER_RGGB
bayer_phase_fix / bayer phase correction
nlm_bayer                      // non-local means denoise in bayer domain
corrupted bayer plane data!
invalid bayer plane size!
non-bayer red coordinate!
```

Strong signal that the internal pipeline is: raw Bayer → phase fix → NLM denoise → color fusion → output. Matches the Light patents and your `lumen_pipeline_stages.md` memory.

---

### 2. liblricompression.dylib — LRI Container Codec

```
Path:     Contents/Frameworks/liblricompression.dylib
Size:     2,837,504 bytes (2.84 MB)
Arch:     Mach-O 64-bit x86_64
Exports:  80 symbols
Links:    libceres.dylib (!), libSystem, libc++
```

**Exported public API:** just two overloads of one function:

```cpp
ltCompress::CompressLRI(std::shared_ptr<istream> const&,
                        std::shared_ptr<ostream> const&,
                        int,     // compression level?
                        bool,    // unknown flag
                        int)     // unknown mode

ltCompress::CompressLRI(std::string const&,  // input path
                        std::string const&,  // output path
                        int, bool, int)
```

The fact that `CompressLRI` links against Ceres is a signal that compression is lossy and uses nonlinear optimization (likely to fit per-module color transforms or depth priors) rather than generic zlib/LZ-style entropy coding. Not merely a repackager.

Only one exported entry point means the **decompress** path is either:
- A private symbol not exported (linkable only if you resolve it via `dlsym` with the mangled name), or
- Inlined into the 80-symbol RTTI/vtable set visible in the export table.

**Decompression is what you actually need** to get raw Bayer planes out of an LRI without running Lumen. The fact it's not publicly exported is the biggest single obstacle to a pure-open reimplementation, and the single highest-value RE target after `libcp`. An afternoon in Ghidra on the 80 symbols should yield a callable decompress routine.

---

### 3. libceres.dylib — Google Ceres Solver (Bundled Dependency)

```
Path:     Contents/Frameworks/libceres.dylib
Size:     2,547,280 bytes
Arch:     Mach-O 64-bit x86_64
Exports:  2,010 symbols
```

This is **not Light's code.** It's a vendored build of the open-source [Ceres Solver](http://ceres-solver.org/) (nonlinear least squares, used for bundle adjustment and camera calibration). Signals:

```
fLB::FLAGS_log_prefix / FLAGS_logtostderr  ← gflags
Eigen::internal::manage_caching_sizes       ← Eigen (Ceres dep)
```

**Do not reverse engineer this.** Swap in upstream Ceres from Homebrew (`brew install ceres-solver`) or vcpkg when you build your replacement. The fact that both libcp and liblricompression link against it is the only reason it's in the bundle.

---

## Tier 2 — Qt 5.11.1 Frameworks (Ignore for RE)

All 22 Qt frameworks in `Contents/Frameworks/Qt*.framework` are stock, unmodified Qt 5.11.1 built with Clang 8.1.0 (Xcode 8.3), released 2018:

```
QtConcurrent  QtCore      QtGui        QtMultimedia     QtMultimediaQuick
QtMultimediaWidgets  QtNetwork     QtOpenGL     QtPrintSupport  QtQml
QtQuick       QtQuickControls2   QtQuickTemplates2    QtQuickTest   QtSql
QtSvg         QtTest      QtWidgets
```

**Reuse guidance:** If you want to resurrect Lumen's UI, rebuild against current Qt 6.x arm64, not these. The QML source and image assets are compiled into Lumen's main binary as Qt resources (`qrc:/Views/ViewToolbar.qml` was visible in the crash log earlier) — see the "UI Assets" section below.

---

## Tier 3 — Qt Plugins (Ignore)

All `.dylib` files under `Contents/PlugIns/` and `Contents/Resources/qml/` are stock Qt plugins (platform integration, image format decoders, SQL drivers, QML components, styles). 60+ files, zero Light code.

```
PlugIns/audio/libqtaudio_coreaudio.dylib
PlugIns/bearer/libqgenericbearer.dylib
PlugIns/iconengines/libqsvgicon.dylib
PlugIns/imageformats/lib{qgif,qicns,qico,qjpeg,qmacheif,qmacjp2,qsvg,qtga,qtiff,qwbmp,qwebp}.dylib
PlugIns/mediaservice/lib{qavfcamera,qavfmediaplayer,qtmedia_audioengine}.dylib
PlugIns/platforms/libqcocoa.dylib
PlugIns/printsupport/libcocoaprintersupport.dylib
PlugIns/quick/lib*.dylib  (~20 files)
PlugIns/sqldrivers/lib{qsqlite,qsqlmysql}.dylib
PlugIns/styles/libqmacstyle.dylib
```

Plus duplicates under `Contents/Resources/qml/Qt/labs/...` for the QML module loader.

**Notably two debug builds** are present (and shipped!):

```
Resources/qml/Qt/labs/platform/libqtlabsplatformplugin_debug.dylib
Resources/qml/Qt/labs/platform/libqtlabsplatformplugin_debug.dylib.dSYM
```

Shipping dSYM in a release bundle is unusual — Light's build system was probably not configured to strip these. Useful only for confirming it's debug Qt, not the Light dev symbols you'd actually want.

---

## What's NOT a library but worth extracting

These live in the main Lumen binary (`Contents/MacOS/Lumen`, not tracked in this inventory) and are reachable without reversing C++:

- **QML views** — compiled into the binary as `qrc:/Views/*.qml` resources. Extractable with `qresource` tools or by dumping `_binary_qt_resource_data` sections. Your memory `project_lumen_ui_as_spec.md` already notes this as the path for UI-as-spec.
- **Images, icons, shaders** — same path, qrc-embedded.
- **Ceres/Halide log strings** — extractable with `strings(1)` from libcp.

---

## Dependency Graph (Linkage)

```
Lumen (main binary, x86_64)
├── @rpath/libcp.dylib
├── @rpath/libceres.dylib
├── @rpath/liblricompression.dylib
├── @rpath/Sparkle.framework/Versions/A/Sparkle
└── Qt 5.11.1 frameworks (all)

libcp.dylib
├── @rpath/libceres.dylib
├── /usr/lib/libSystem.B.dylib
└── /usr/lib/libc++.1.dylib

liblricompression.dylib
├── @rpath/libceres.dylib
├── /usr/lib/libSystem.B.dylib
└── /usr/lib/libc++.1.dylib

libceres.dylib
├── /usr/lib/libSystem.B.dylib
└── /usr/lib/libc++.1.dylib
```

**Key observation:** Lumen links directly against `libcp`, `libceres`, `liblricompression`, and Sparkle — nothing else Light-proprietary exists. All processing goes through those three dylibs. If you link a new binary against the same three, you have functional parity with Lumen minus the UI.

---

## Recommended Reverse-Engineering Work Plan

Ordered by value per hour of effort. Each item is independent — parallelize any that aren't blocked.

### Phase 1 — Link & call (no RE needed, ~1 day)

1. **Write a ctypes / cffi wrapper for `CIAPI::Renderer`** — enumerate the exported mangled names, demangle, generate Python bindings. Start with `GetVersion()` as smoke test, then `Renderer::Renderer(shared_ptr<RendererPrivate>)` + `deserialize` + `writeImage(..., ExportImageFormat::DNG, ...)`. This alone gets you ground-truth DNG export without the Lumen GUI.
2. **Wrap `ltCompress::CompressLRI`** — trivial, only 2 overloads. Confirms you can round-trip an LRI.
3. **Force arm64 via Rosetta-linked thin wrapper.** Build a tiny x86_64 wrapper binary that ctypes can `dlopen` under Rosetta, invoked from an arm64 Python via subprocess. Avoids needing arm64 builds of Qt.

### Phase 2 — Reverse the decompress path (~2–5 days)

4. **Static-analyze `liblricompression.dylib` in Ghidra.** Find the private decompression function (it's one of the 80 exported symbols — look for something paired with `CompressLRI` in the vtable or RTTI). Document the calling convention and produce a standalone C reimplementation.
5. **Reimplement LRI container parsing in Rust/Python** based on the Ghidra output, validated against `ltCompress::CompressLRI` round-trip.

### Phase 3 — Reverse the fusion kernels (~weeks)

6. **Map `lt::ColorFusionBayer` and `lt::FusionCacheBayer`** in Ghidra. Find vtables from RTTI strings. Dump method bodies.
7. **Identify Halide-generated kernels** by buffer-passing convention and cross-reference to the named fusion types.
8. **Re-implement fusion in modern Halide** or plain Rust/OpenCL. Validate pixel-for-pixel against Lumen's `writeImage` output from Phase 1.

### Phase 4 — UI asset extraction (optional, ~1 day)

9. **Dump `qrc:/` resources** from `Contents/MacOS/Lumen` using `rcc -binary` in reverse, or `qresource-extractor`. Gives you QML, images, shaders for the "Lumen UI as spec" memory goal.

---

## Caveats & Anti-Patterns

- **Don't bind against these dylibs and ship it.** Your memory `project_no_lumen_binary_dependency.md` explicitly forbids runtime dependency on Lumen binaries for shipped code. Phases 1–2 are for RE and validation only; anything shippable must be rewritten.
- **Don't try to run libcp on arm64 natively.** It's x86_64; the Halide kernels are AOT-compiled for x86_64. You'd be reimplementing, not porting.
- **Don't trust `lri_process` CLI output for DNG ground truth.** Per `project_lri_process_cli.md`, `--export-fmt 4` writes JPEGs with `.dng` extensions. The real DNG path is `Renderer::writeImage(..., DNG, ...)`, which is only reached from Phase 1 above or from the Lumen GUI (which doesn't run on Apple Silicon).
- **Ceres is a red herring.** Don't reverse it. Link upstream.
- **Qt 5.11.1 is also a red herring.** The macOS Apple Silicon failure is a Qt version issue, not a Lumen issue. Rebuilding Lumen's own code against Qt 6 arm64 would probably "just work" if you had the source — but you don't, and that's the whole point of RE.

---

## Appendix — Raw enumeration commands

All findings above were produced by these commands against `Contents/` of the bundle:

```bash
# Find every native library
find . \( -name '*.dylib' -o -name '*.framework' -o -name '*.a' \) -print

# Classify arch + size
file Frameworks/libcp.dylib
stat -f '%z' Frameworks/libcp.dylib

# Enumerate exported symbols and demangle
nm -gU Frameworks/libcp.dylib | c++filt

# Extract CIAPI namespace surface
nm -gU Frameworks/libcp.dylib | c++filt | grep -oE 'CIAPI::[A-Za-z_]+' | sort -u

# Linkage
otool -L Frameworks/libcp.dylib
otool -L MacOS/Lumen

# String mining for internal types and format hints
strings -a Frameworks/libcp.dylib | grep -iE '(bayer|halide|DNGWriter|ColorMatrix)'
```
