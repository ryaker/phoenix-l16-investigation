// lri_process.cpp — Light L16 LRI → DNG / HDR / TIFF converter
//
// Calls Light's own libcp.dylib (CIAPI namespace) directly.
// No reverse engineering: every symbol is exported and demangled.
// No auth: the library has zero network dependencies.
//
// ── Object layout verified by disassembling DirectRenderer::Create ──
//   DirectRenderer::Create allocates a RendererBasePrivate on the heap,
//   builds a shared_ptr, calls RendererBase::RendererBase(shared_ptr<...>),
//   then overwrites *(this) with the DirectRenderer vtable pointer.
//   DirectRenderer adds NO extra data members beyond RendererBase.
//
//   RendererBase layout: [vtptr(8)] + [shared_ptr<Private>(16)] = 24 bytes
//   DirectRenderer layout: identical (just different vtable pointer)
//   Renderer layout: identical (just different vtable pointer)
//   Image layout: [shared_ptr<Private>(16)] = 16 bytes (non-polymorphic)
//   ImagePyramid layout: [shared_ptr<Private>(16)] = 16 bytes (non-polymorphic)
//
// ── Confirmed enum values (from Lumen.app / libcp.dylib disassembly) ──
//   RendererProfile::Desktop = 3       (movl $0x3, %esi before Renderer::Create)
//   RenderType::Export       = 2       (movl $0x2, %edx in export code path)
//   TuningType::Default      = 0       (ApplyTuning called with 0 at every call site)
//   StateType::Normal        = 0       (xorl %edx, %edx before Renderer::deserialize
//                                        in StreamEditor::deserializeFrom)
//
// ── Confirmed ExportImageFormat values (empirical probe) ──
//   0 = JPEG                           (lt::JpegWriter)
//   1 = PPM lossless 8-bit RGB         (lt::Internal::ParserPPM)
//   2 = TIFF JPEG-compressed           (lt::TiffIFD)
//   3 = Radiance HDR 32-bit float      (lt::Internal::ParserHDR) ← best for AI pipeline
//   4 = DPC/DNG with depth             (lt::Internal::ParserDPC) ← requires LRIS state
//   5+ = throws "Unexpected export format!"
//
// ── DPC/DNG export ──
//   Format 4 embeds a depth map (Google Depth Map XMP: GDepth:Data,
//   GDepth:Format="RangeInverse") in a DNG container.  Requires a
//   matching .lris file (Light's state file, written by Lumen).
//   Load it via Renderer::deserialize(stream, StateType(0)) BEFORE render().
//   The tool auto-detects a same-named .lris alongside the .lri unless
//   --no-auto-lris is passed, or you can specify --lris <path>.
//
// ── Build ──
//   See build.sh in the same directory.
//
// ── Run ──
//   arch -x86_64 ./lri_process input.lri out.hdr           # HDR (default)
//   arch -x86_64 ./lri_process input.lri out.dng           # DPC/DNG (auto-detects .lris)
//   arch -x86_64 ./lri_process input.lri out.dng --lris input.lris  # explicit LRIS
//   arch -x86_64 ./lri_process input.lri out.tiff --direct-renderer # fast fallback

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <string>
#include <fstream>
#include <functional>
#include <vector>
#include <atomic>
#include <CoreFoundation/CoreFoundation.h>
#include <ImageIO/ImageIO.h>

// ============================================================
// CIAPI class stubs
// Declaration-only: no definitions.  All symbols are resolved
// from libcp.dylib by the linker at build time.
// ============================================================

// ── opaque private types (never instantiated) ──
namespace lt {
    struct RendererBasePrivate;
    struct DirectRendererPrivate;
    struct RendererPrivate;
    struct DepthEditorPrivate;  // Added 2026-04-18 for depth-pipeline unlock
}
namespace CIAPI {
    namespace Internal {
        struct ImagePrivate;
        struct ImagePyramidPrivate;
    }
}

namespace CIAPI {

struct ROI    { int x, y, width, height; };
template<class T> struct Point { T x, y; };

// ── Enum types — must match mangled names in libcp.dylib ────
// Values confirmed by disassembling Lumen.app and libcp.dylib.
enum RendererProfile   : int {};
enum RenderType        : int {};
enum ExportImageFormat : int {};
enum TuningType        : int {};
// StateType::Normal = 0 (confirmed: StreamEditor::deserializeFrom passes 0)
enum StateType         : int {};
// RenderingMode: 2 = depth-active (gates StereoAsyncAPI + DepthCache pipeline).
// Without setMode(2) + DepthEditor ctor, vtable slot 20 of RendererPrivate at
// libcp+0x3b1d20 is never dispatched and depth code stays silent.
enum RenderingMode     : int {};
enum ParamFloat        : int {};
enum ParamInt          : int {};

// ── Image ────────────────────────────────────────────────────
// Non-polymorphic.  Layout: shared_ptr<ImagePrivate> = 16 bytes.
//
// Image has a non-trivial copy ctor/dtor (shared_ptr refcounting).
// The SysV ABI therefore returns Image via hidden pointer (rdi).
// This matches Image::Create in the dylib.
//
// DirectRenderer::render() returns VOID (confirmed from disassembly: no value
// loaded into rax before retq).  It writes the result into the Image& arg.
// Declaring render() void eliminates any hidden-pointer confusion there.
class Image {
public:
    enum PixelFormat : int { Unknown = 0 };

    // Factory — allocates an Image with a caller-owned or library-owned buffer.
    // plane_stride must be 0 for packed formats; set to (stride*h) for planar (fmt=3).
    static Image Create(int w, int h, PixelFormat fmt,
                        int stride, int plane_stride, void* data);

    Image();
    ~Image();
    Image(const Image&);
    Image& operator=(const Image&);

    bool          empty()       const;
    void*         data()        const;
    int           width()       const;
    int           height()      const;
    int           stride()      const;  // bytes per row
    int           planeStride() const;
    PixelFormat   pixelFormat() const;

private:
    // shared_ptr<Internal::ImagePrivate> — two void* = 16 bytes
    std::shared_ptr<Internal::ImagePrivate> impl_;
};

// ── ImagePyramid ─────────────────────────────────────────────
// Non-polymorphic.  Layout: shared_ptr<ImagePyramidPrivate> = 16 bytes.
// Returned via hidden pointer (non-trivial copy ctor/dtor).
// operator[] returns a reference to the selected 16-byte Image element.
class ImagePyramid {
public:
    ~ImagePyramid();
    ImagePyramid(const ImagePyramid&);
    ImagePyramid& operator=(const ImagePyramid&);

    Image&       operator[](int level);
    Image const& operator[](int level) const;
    int   levelCount() const;
    void  lock()   const;
    void  unlock() const;

private:
    // shared_ptr<Internal::ImagePyramidPrivate> — two void* = 16 bytes
    std::shared_ptr<Internal::ImagePyramidPrivate> impl_;
};

// ── Transform ────────────────────────────────────────────────
// Non-polymorphic. Lives inline inside RendererPrivate at offset 0xb0.
// RendererBase::transform() returns a pointer to it.
// aspectRatio() returns packed 64-bit: lo32 = full_width, hi32 = full_height.
// These are the native image dimensions BEFORE any crop, available before render().
class Transform {
public:
    // Returns packed {lo32=width, hi32=height} of the native (uncropped) image.
    // Confirmed from libcp disassembly: reads offsets +8, +12 of Transform private data.
    long long aspectRatio() const;
};

// ── RendererBase ─────────────────────────────────────────────
// Polymorphic base.  Layout: [vtptr(8)] + [shared_ptr<Private>(16)] = 24 bytes.
//
// Declared non-polymorphic in this stub (no 'virtual' keyword) to
// avoid emitting a competing vtable from this TU.  The actual
// vtable pointer is written into vtptr_ by Renderer::Create() /
// DirectRenderer::Create().
// Our code calls all methods non-virtually by mangled name.
class RendererBase {
public:
    // Declared on RendererBase in the dylib — linker finds _ZN5CIAPI12RendererBase...
    void setInputDataStream(std::shared_ptr<std::istream> const&);
    void setInputDataStream(void const* buf, size_t len);

    // Returns pointer to inline Transform (at RendererPrivate+0xb0).
    // Valid after setInputDataStream() — contains native image dimensions.
    Transform* transform();

    // ParamFloat(19) is the validated MaximumInFocusBlurPixels control.
    void setProperty(ParamFloat, float);
    void setProperty(ParamInt, int);

    ~RendererBase();

protected:
    RendererBase();
    explicit RendererBase(std::shared_ptr<lt::RendererBasePrivate> const&);

private:
    // ── exact 24-byte layout ──
    void*                 vtptr_; // real vtable ptr written by Create()
    std::shared_ptr<void> impl_;  // shared_ptr<RendererBasePrivate> (16 bytes)
};

// ── Renderer : RendererBase ───────────────────────────────────
// Full-quality async-capable renderer.  Used by Lumen for DNG export.
// Adds no data members beyond RendererBase (same 24-byte layout).
//
// Usage:
//   Renderer r = Renderer::Create(RendererProfile(3));   // Desktop quality
//   r.setInputDataStream(stream);
//   ApplyTuning(TuningType(0), r);                        // camera calibration
//   r.render(0, {0,0,65536,65536}, RenderType(2), true);  // wait for full image
//   ImagePyramid pyr = r.outputBuffer();
//   Image lvl0 = pyr[0];
//   auto out = make_shared<ofstream>(path, ios::binary);
//   r.writeImage(out, {lvl0.width(), lvl0.height()}, ExportImageFormat(1), cb);
class Renderer : public RendererBase {
public:
    // Factory — RendererProfile 3 = Desktop (confirmed from Lumen disassembly)
    static Renderer Create(RendererProfile profile);

    // Synchronous full-quality render.
    // resolution=0 (base level), roi clamped to image bounds, RenderType=2 (export).
    void render(int resolution, ROI const& roi, RenderType type, bool wait);

    // Write output to stream.  Point<int> = {output_width, output_height}.
    // ExportImageFormat 3=HDR, 4=DPC/DNG (requires LRIS state loaded first).
    // Callback receives progress 0–100.
    void writeImage(std::shared_ptr<std::ostream> const&,
                    Point<int> const&,
                    ExportImageFormat,
                    std::function<void(int)>);

    // Load LRIS state file (Light's processed state with depth map).
    // StateType=0 is what Lumen uses (confirmed from StreamEditor::deserializeFrom).
    // Must be called AFTER setInputDataStream(), BEFORE render().
    // Required for DPC/DNG export (ExportImageFormat=4).
    void deserialize(std::shared_ptr<std::istream> const&, StateType);

    // Set the rendering mode. RenderingMode(2) = depth-active.
    // Stores the int at RendererPrivate+0x774. The render worker thread checks
    // `cmpl $0x2, 0x774` at libcp+0x3b0874 to gate the depth dispatch.
    // Without this, the depth pipeline (StereoAsyncAPI + DepthCache) never fires
    // even on bridge fmt=4 (which still passes through .lris depth, not live compute).
    void setMode(RenderingMode);

    // Save current rendering state to stream (LRIS format).
    void serialize(std::shared_ptr<std::ostream> const&, StateType);

    // Returns the rendered output pyramid.  Level 0 is full resolution.
    ImagePyramid outputBuffer() const;

    void setOutputUpdateListener(
        std::function<void(ImagePyramid const&, ROI const&, int)> listener);

    void abort();
    void cancelRenderRequests();

    ~Renderer();
    Renderer(const Renderer&);
    Renderer& operator=(const Renderer&);

private:
    Renderer() = delete;
    explicit Renderer(std::shared_ptr<lt::RendererPrivate> const&);
};

// ── DepthEditor ──────────────────────────────────────────────
// Non-polymorphic.  Layout: shared_ptr<DepthEditorPrivate> = 16 bytes.
// Forwarding wrapper: 14 method exports at libcp+0x395ff0..0x3961b0,
// each thunking into lt::DepthEditorPrivate::*.
//
// Constructing a DepthEditor(Renderer&) registers a shared_ptr observer at
// RendererPrivate+0x50.  This + setMode(RenderingMode(2)) is the gate that
// unlocks the depth pipeline (StereoAsyncAPI ctor + DepthCache ctor inside
// the worker-thread render path at RendererPrivate vtable slot 20 = libcp+0x3b1d20).
//
// IMPORTANT: libcp does NOT export DepthEditor::~DepthEditor.  We declare a
// trivial inline dtor here that does NOT decrement the shared_ptr refcount.
// The shared_ptr-control-block memory leaks at program exit — acceptable for
// a one-shot bridge tool; would need a hidden-symbol resolver for long-running use.
class DepthEditor {
public:
    explicit DepthEditor(Renderer& renderer);
    ~DepthEditor() {}  // intentionally trivial — see note above
    float getDepthAtPoint(Point<float> const& point);
    void pushBrushDepthEdit(struct BrushDepthEditingParams const& params);
    void addQuickSelectStrokes(
        struct QuickSelectDepthEditingParams const& params);
private:
    DepthEditor() = delete;
    DepthEditor(const DepthEditor&) = delete;
    DepthEditor& operator=(const DepthEditor&) = delete;
    // 16 bytes matching shared_ptr<DepthEditorPrivate>; treated as opaque.
    void* private_ptr_  = nullptr;
    void* private_ctrl_ = nullptr;
};

struct BrushDepthEditingParams {
    std::vector<Point<float>> points;
    float radius;
    float depth;
    bool reserved;
};

// Public packet layout recovered from ImageEditItem::addQuickSelectStrokes.
// ROI stores the half-open level rectangle as x0,y0,x1,y1 for this API.
struct QuickSelectDepthEditingParams {
    std::vector<Point<float>> points;
    float radius;
    bool mode;
    ROI level_rect;
    int level;
};

// ── DirectRenderer : RendererBase ────────────────────────────
// Simplified synchronous renderer (faster but lower quality / blurry).
// Adds no data members beyond RendererBase.
class DirectRenderer : public RendererBase {
public:
    // Factory — profile=0 is the only verified value; try 1,2,3 if render() fails
    static DirectRenderer Create(int profile = 0);

    // Renders into the Image& argument (confirmed void return from disassembly).
    void render(Image&);

    int width()  const;
    int height() const;

    ~DirectRenderer();
    DirectRenderer(const DirectRenderer&);
    DirectRenderer& operator=(const DirectRenderer&);

private:
    DirectRenderer() = delete;
    explicit DirectRenderer(std::shared_ptr<lt::DirectRendererPrivate> const&);
    // No extra members — DirectRenderer only overrides the vtable
};

// ── free functions ───────────────────────────────────────────
std::string GetVersion();
void        StaticShutdown();

// Apply camera calibration tuning.  TuningType 0 = default.
// Must be called after setInputDataStream() and before render().
void ApplyTuning(TuningType type, RendererBase& renderer);

} // namespace CIAPI

// ============================================================
// Pixel format helpers (used by --direct-renderer path)
// ============================================================

// Guess bytes-per-pixel from observed stride/width ratio.
static int guess_bpp(int stride, int width) {
    if (width <= 0) return 4;
    int r = stride / width;
    if (r == 4 || r == 3 || r == 8 || r == 6) return r;
    return 4; // default to RGBA8
}

// Attempt to write a TIFF using macOS ImageIO.
static bool write_tiff(const char* path,
                       int w, int h, int stride,
                       void* data, int fmt_int)
{
    int bpp = guess_bpp(stride, w);
    printf("  Pixel format int: %d, bpp guess: %d\n", fmt_int, bpp);

    CGBitmapInfo info;
    size_t       bpc;
    size_t       nc;

    switch (bpp) {
    case 4:  bpc = 8;  nc = 4; info = kCGBitmapByteOrder32Big | kCGImageAlphaPremultipliedLast; break;
    case 3:  bpc = 8;  nc = 3; info = kCGBitmapByteOrderDefault | kCGImageAlphaNone; break;
    case 8:  bpc = 16; nc = 4; info = kCGBitmapByteOrder16Big   | kCGImageAlphaPremultipliedLast; break;
    case 6:  bpc = 16; nc = 3; info = kCGBitmapByteOrder16Big   | kCGImageAlphaNone; break;
    default: bpc = 8;  nc = 4; info = kCGBitmapByteOrder32Big | kCGImageAlphaPremultipliedLast; break;
    }
    (void)nc;

    CGColorSpaceRef cs  = CGColorSpaceCreateDeviceRGB();
    CGContextRef    ctx = CGBitmapContextCreate(data, (size_t)w, (size_t)h,
                                                bpc, (size_t)stride, cs, info);
    CGColorSpaceRelease(cs);

    if (!ctx) {
        fprintf(stderr, "  CGBitmapContextCreate failed (fmt_int=%d bpp=%d)\n", fmt_int, bpp);
        return false;
    }

    CGImageRef img = CGBitmapContextCreateImage(ctx);
    CGContextRelease(ctx);
    if (!img) { fprintf(stderr, "  CGBitmapContextCreateImage failed\n"); return false; }

    CFURLRef url = CFURLCreateFromFileSystemRepresentation(
        kCFAllocatorDefault, (const UInt8*)path, (CFIndex)strlen(path), false);

    CGImageDestinationRef dest = CGImageDestinationCreateWithURL(url, CFSTR("public.tiff"), 1, nullptr);
    CFRelease(url);

    if (!dest) {
        CGImageRelease(img);
        fprintf(stderr, "  CGImageDestinationCreateWithURL failed\n");
        return false;
    }

    CGImageDestinationAddImage(dest, img, nullptr);
    bool ok = (bool)CGImageDestinationFinalize(dest);
    CFRelease(dest);
    CGImageRelease(img);
    return ok;
}

// Write raw pixel bytes + sidecar .info file.
static void write_raw(const char* tiff_path, int w, int h, int stride,
                      void* data, int fmt_int)
{
    char raw_path[4096], info_path[4096];
    snprintf(raw_path,  sizeof(raw_path),  "%s.raw",  tiff_path);
    snprintf(info_path, sizeof(info_path), "%s.info", tiff_path);

    FILE* f = fopen(raw_path, "wb");
    if (f) {
        fwrite(data, 1, (size_t)(stride * h), f);
        fclose(f);
        printf("  Raw dump  → %s\n", raw_path);
    }

    FILE* g = fopen(info_path, "w");
    if (g) {
        fprintf(g, "width=%d\nheight=%d\nstride=%d\npixelformat_int=%d\nbytes=%d\n",
                w, h, stride, fmt_int, stride * h);
        fclose(g);
        printf("  Info file → %s\n", info_path);
    }

    int bpp = guess_bpp(stride, w);
    const char* pix_fmt = (bpp == 4) ? "rgba"  :
                          (bpp == 3) ? "rgb24" :
                          (bpp == 8) ? "rgba64be" :
                                       "rgba";
    printf("\n  To convert raw with ffmpeg:\n");
    printf("  ffmpeg -f rawvideo -pixel_format %s -video_size %dx%d "
           "-i \"%s\" \"%s.png\"\n\n", pix_fmt, w, h, raw_path, tiff_path);
}

extern "C" __attribute__((noinline))
void lri_probe_output_write_target(void* address, int level, int x, int y)
{
    asm volatile("" : : "r"(address), "r"(level), "r"(x), "r"(y) : "memory");
}

// ============================================================
// Main
// ============================================================
int main(int argc, char* argv[])
{
    if (argc < 3) {
        fprintf(stderr,
            "Usage: arch -x86_64 ./lri_process <input.lri> <output.hdr|.dng|.jpg|.ppm|.tif>\n\n"
            "Full-quality Renderer path options:\n"
            "  --profile N          RendererProfile 0–3 (default 3 = Desktop quality)\n"
            "  --render-type N      Renderer request type (default 2 = export; GUI tiles use 1)\n"
            "  --render-only        Stop after render(); do not call the export writer\n"
            "  --sync-render        Wait for the queued render request to finish\n"
            "  --renderer-mode N    Set Renderer RenderingMode 0-4 before input\n"
            "  --debug-view-id N    Set debug-view selector ParamInt(20), accepts decimal or 0x hex\n"
            "  --maximum-in-focus-blur-pixels F Set validated ParamFloat(19) before mode switch\n"
            "  --dof-f-number F    Set public ParamFloat(0) before prepared mode switch\n"
            "  --dof-focus-depth F Set public ParamFloat(1) before prepared mode switch\n"
            "  --dof-focus-center  Use DepthEditor center depth for public ParamFloat(1)\n"
            "  --prepare-mode0-rerender Render mode 0 once, then set requested mode and rerender\n"
            "  --construct-depth-editor Construct DepthEditor without applying a brush\n"
            "  --brush-edit-rerender Apply one synthetic depth brush, then render again\n"
            "  --quick-select-center Add one synthetic center QuickSelect stroke before rerender\n"
            "  --gui-level-sweep    Render every output-pyramid level coarse to fine\n"
            "  --inspect-output-pyramid Print output-pyramid image metadata after render\n"
            "  --dump-output-level N PATH Dump one packed pyramid level as PATH.raw/.info\n"
            "  --probe-output-level N Mark one level-N pixel for an LLDB write watchpoint\n"
            "  --output-size W H    Override export writer dimensions (probe use)\n"
            "  --export-fmt N       Output format: 0=JPEG 1=PPM 2=TIFF 3=HDR 4=DNG (default 3)\n"
            "  --lris <path>        Explicit .lris state file path (required for --export-fmt 4)\n"
            "                       Auto-detected if <input>.lris exists beside the .lri\n"
            "  --no-auto-lris      Do not auto-detect a same-named .lris sidecar\n"
            "  --no-lris           Do not load any .lris state, explicit or auto-detected\n"
            "  --write-lris <path>  Serialize render state (depth) to .lris after render\n"
            "\n"
            "DirectRenderer fallback (faster, lower quality):\n"
            "  --direct-renderer    Use DirectRenderer → TIFF output\n"
            "  --dr-profile N       DirectRenderer profile (default 1; valid 1–4)\n"
            "  --no-tiff            Write raw pixel dump instead of TIFF\n\n"
            "Examples:\n"
            "  arch -x86_64 ./lri_process L16_00001.lri out.hdr\n"
            "  arch -x86_64 ./lri_process L16_00001.lri out.dng   # auto-finds L16_00001.lris\n"
            "  arch -x86_64 ./lri_process L16_00001.lri out.dng --lris /path/to/L16_00001.lris\n");
        return 1;
    }

    const char* input_path   = argv[1];
    const char* output_path  = argv[2];
    int         profile      = 3;    // RendererProfile::Desktop
    int         render_type  = 2;    // RenderType::Export
    int         export_fmt   = 3;    // ExportImageFormat: 3=Radiance HDR (best quality)
    int         dr_profile   = 1;    // DirectRenderer profile (1=full res)
    bool        use_direct   = false;
    bool        render_only  = false;
    bool        sync_render  = false;
    int         renderer_mode = -1;
    int         debug_view_id = -1;
    float       maximum_in_focus_blur_pixels = -1.0f;
    float       dof_f_number = -1.0f;
    float       dof_focus_depth = -1.0f;
    bool        dof_focus_center = false;
    bool        prepare_mode0_rerender = false;
    bool        construct_depth_editor = false;
    bool        brush_edit_rerender = false;
    bool        quick_select_center = false;
    bool        gui_level_sweep = false;
    bool        inspect_output_pyramid = false;
    int         probe_output_level = -1;
    int         dump_output_level = -1;
    const char* dump_output_path = nullptr;
    int         output_width = 10432;
    int         output_height = 7824;
    bool        write_tiff_  = true;
    const char* lris_path       = nullptr; // explicit .lris path (or auto-detected)
    const char* write_lris_path = nullptr; // path to serialize fresh render state
    bool        auto_lris       = true;
    bool        disable_lris    = false;

    for (int i = 3; i < argc; i++) {
        if (strcmp(argv[i], "--profile") == 0 && i+1 < argc)
            profile = atoi(argv[++i]);
        else if (strcmp(argv[i], "--render-type") == 0 && i+1 < argc)
            render_type = atoi(argv[++i]);
        else if (strcmp(argv[i], "--render-only") == 0)
            render_only = true;
        else if (strcmp(argv[i], "--sync-render") == 0)
            sync_render = true;
        else if (strcmp(argv[i], "--renderer-mode") == 0 && i+1 < argc)
            renderer_mode = atoi(argv[++i]);
        else if (strcmp(argv[i], "--debug-view-id") == 0 && i+1 < argc)
            debug_view_id = static_cast<int>(strtol(argv[++i], nullptr, 0));
        else if (strcmp(argv[i], "--maximum-in-focus-blur-pixels") == 0 && i+1 < argc)
            maximum_in_focus_blur_pixels = strtof(argv[++i], nullptr);
        else if (strcmp(argv[i], "--dof-f-number") == 0 && i+1 < argc)
            dof_f_number = strtof(argv[++i], nullptr);
        else if (strcmp(argv[i], "--dof-focus-depth") == 0 && i+1 < argc)
            dof_focus_depth = strtof(argv[++i], nullptr);
        else if (strcmp(argv[i], "--dof-focus-center") == 0)
            dof_focus_center = true;
        else if (strcmp(argv[i], "--prepare-mode0-rerender") == 0)
            prepare_mode0_rerender = true;
        else if (strcmp(argv[i], "--construct-depth-editor") == 0)
            construct_depth_editor = true;
        else if (strcmp(argv[i], "--brush-edit-rerender") == 0)
            brush_edit_rerender = true;
        else if (strcmp(argv[i], "--quick-select-center") == 0)
            quick_select_center = true;
        else if (strcmp(argv[i], "--gui-level-sweep") == 0)
            gui_level_sweep = true;
        else if (strcmp(argv[i], "--inspect-output-pyramid") == 0)
            inspect_output_pyramid = true;
        else if (strcmp(argv[i], "--probe-output-level") == 0 && i+1 < argc)
            probe_output_level = atoi(argv[++i]);
        else if (strcmp(argv[i], "--dump-output-level") == 0 && i+2 < argc) {
            dump_output_level = atoi(argv[++i]);
            dump_output_path = argv[++i];
        }
        else if (strcmp(argv[i], "--output-size") == 0 && i+2 < argc) {
            output_width = atoi(argv[++i]);
            output_height = atoi(argv[++i]);
        }
        else if (strcmp(argv[i], "--export-fmt") == 0 && i+1 < argc)
            export_fmt = atoi(argv[++i]);
        else if (strcmp(argv[i], "--direct-renderer") == 0)
            use_direct = true;
        else if (strcmp(argv[i], "--dr-profile") == 0 && i+1 < argc)
            dr_profile = atoi(argv[++i]);
        else if (strcmp(argv[i], "--no-tiff") == 0)
            write_tiff_ = false;
        else if (strcmp(argv[i], "--lris") == 0 && i+1 < argc)
            lris_path = argv[++i];
        else if (strcmp(argv[i], "--no-auto-lris") == 0)
            auto_lris = false;
        else if (strcmp(argv[i], "--no-lris") == 0) {
            auto_lris = false;
            disable_lris = true;
            lris_path = nullptr;
        }
        else if (strcmp(argv[i], "--write-lris") == 0 && i+1 < argc)
            write_lris_path = argv[++i];
    }

    if (disable_lris)
        lris_path = nullptr;

    // Auto-detect .lris if output extension is .dng and no explicit --lris given.
    // Also auto-detect if a same-named .lris exists alongside the .lri.
    std::string auto_lris_path;
    if (!lris_path && auto_lris) {
        // Build candidate: replace .lri extension with .lris
        std::string inp(input_path);
        std::string candidate;
        auto dot = inp.rfind('.');
        if (dot != std::string::npos)
            candidate = inp.substr(0, dot) + ".lris";
        else
            candidate = inp + ".lris";

        // Check if .dng output was requested via extension
        std::string out(output_path);
        auto odot = out.rfind('.');
        bool dng_output = (odot != std::string::npos &&
                           strcasecmp(out.c_str() + odot, ".dng") == 0);

        // If .dng output requested but no --export-fmt specified, switch to fmt=4
        if (dng_output && export_fmt == 3)
            export_fmt = 4;

        // Auto-use .lris if it exists (needed for fmt=4; harmless otherwise)
        std::ifstream test(candidate, std::ios::binary);
        if (test.is_open()) {
            auto_lris_path = candidate;
            lris_path = auto_lris_path.c_str();
            printf("  LRIS auto-detected: %s\n", lris_path);
        } else if (export_fmt == 4) {
            fprintf(stderr,
                "WARNING: DNG output (fmt=4) requested but no .lris state file found.\n"
                "         Auto-looked for: %s\n"
                "         Specify --lris <path> or the output may be empty.\n",
                candidate.c_str());
        }
    }

    // ── Safety: refuse to overwrite LRI files ────────────────
    {
        const char* ext = strrchr(output_path, '.');
        if (ext && (strcasecmp(ext, ".lri") == 0)) {
            fprintf(stderr, "ERROR: output path ends in .lri — refusing to overwrite source photos.\n"
                            "       Specify a .dng or .tiff output path.\n");
            return 1;
        }
        if (strcmp(input_path, output_path) == 0) {
            fprintf(stderr, "ERROR: input and output paths are the same — refusing.\n");
            return 1;
        }
    }

    // ── Open LRI file (read-only) ─────────────────────────────
    auto stream = std::make_shared<std::ifstream>(input_path, std::ios::binary);
    if (!stream->is_open()) {
        fprintf(stderr, "Cannot open: %s\n", input_path);
        return 1;
    }

    // ── DirectRenderer path (fallback, TIFF output) ──────────
    if (use_direct) {
        CIAPI::DirectRenderer renderer = CIAPI::DirectRenderer::Create(dr_profile);
        renderer.setInputDataStream(stream);

        int rw = renderer.width();
        int rh = renderer.height();
        printf("%s → %s  [%dx%d dr_profile=%d]\n",
               input_path, output_path, rw, rh, dr_profile);
        fflush(stdout);

        const int stride0 = rw * 4;
        std::vector<uint8_t> pixels((size_t)stride0 * rh, 0);
        CIAPI::Image out_buf = CIAPI::Image::Create(rw, rh,
                                   CIAPI::Image::PixelFormat::Unknown,
                                   stride0, 0, pixels.data());

        try {
            renderer.render(out_buf);
        } catch (const std::exception& e) {
            fprintf(stderr, "render() failed: %s\n", e.what());
            CIAPI::StaticShutdown();
            return 1;
        }

        if (out_buf.empty()) {
            fprintf(stderr, "Render produced empty image (dr_profile=%d, try 1–4)\n", dr_profile);
            CIAPI::StaticShutdown();
            return 1;
        }

        int   w      = out_buf.width();
        int   h      = out_buf.height();
        int   stride = out_buf.stride();
        void* data   = out_buf.data();
        int   fmt    = (int)out_buf.pixelFormat();

        if (!data || w <= 0 || h <= 0) {
            fprintf(stderr, "Invalid image output\n");
            CIAPI::StaticShutdown();
            return 1;
        }

        if (write_tiff_) {
            if (write_tiff(output_path, w, h, stride, data, fmt))
                printf("  TIFF written (%dx%d)\n", w, h);
            else {
                fprintf(stderr, "TIFF write failed — writing raw instead\n");
                write_raw(output_path, w, h, stride, data, fmt);
            }
        } else {
            write_raw(output_path, w, h, stride, data, fmt);
        }

        CIAPI::StaticShutdown();
        return 0;
    }

    // ── Full-quality Renderer path ────────────────────────────
    // ExportImageFormat map (confirmed by probing all values):
    //   0 = JPEG
    //   1 = PPM  (lossless 8-bit RGB)
    //   2 = TIFF (JPEG-compressed)
    //   3 = Radiance HDR (32-bit float RGB — best quality for AI pipeline)
    //   4 = DPC/DNG with embedded depth map (requires LRIS state loaded first)
    //   5+ = throws "Unexpected export format!"

    static const char* fmt_name[] = {"JPEG", "PPM", "TIFF", "HDR", "DNG"};
    const char* fname = (export_fmt >= 0 && export_fmt <= 4) ? fmt_name[export_fmt] : "?";
    printf("%s → %s  [profile=%d render_type=%d fmt=%d(%s)%s]\n",
           input_path, output_path, profile, render_type, export_fmt, fname,
           (lris_path ? " +lris" : ""));
    fflush(stdout);

    CIAPI::Renderer renderer = [&]() -> CIAPI::Renderer {
        try {
            return CIAPI::Renderer::Create(static_cast<CIAPI::RendererProfile>(profile));
        } catch (const std::exception& e) {
            fprintf(stderr, "Renderer::Create failed: %s\n", e.what());
            CIAPI::StaticShutdown();
            exit(1);
        }
    }();
    std::unique_ptr<CIAPI::DepthEditor> depth_editor;
    if (construct_depth_editor || brush_edit_rerender || quick_select_center)
        depth_editor = std::make_unique<CIAPI::DepthEditor>(renderer);

    std::atomic<int> output_update_count{0};
    if (inspect_output_pyramid || dump_output_path || probe_output_level >= 0) {
        renderer.setOutputUpdateListener(
            [&output_update_count](CIAPI::ImagePyramid const&, CIAPI::ROI const&, int) {
                output_update_count.fetch_add(1, std::memory_order_relaxed);
            });
    }

    // NOTE 2026-04-18: removed --depth gate (setMode(2) + DepthEditor ctor).
    // Verification proved depth pipeline (DepthCache + StereoAsyncAPI + Triangulator)
    // already fires unconditionally on bridge fmt=4 — the real gate is at
    // libcp+0x3b2fa3 checking [imageStorageObj+0] & 0xf == 0x3 (set by export
    // path), not RenderingMode. setMode(2) was a misdiagnosis.
    // See depth_unlock_verification.md for the 4-scenario hit-count proof.

    try { renderer.setInputDataStream(stream); }
    catch (const std::exception& e) {
        fprintf(stderr, "setInputDataStream failed: %s\n", e.what());
        CIAPI::StaticShutdown();
        return 1;
    }

    // ── Load LRIS state file (if available) ──────────────────
    // The .lris file was written by Lumen and contains:
    //   - Processed depth map (used by DPC/DNG export)
    //   - Rendering state (depth edits, crop, colour adjustments)
    // StateType=0 is what Lumen passes (confirmed from disassembly of
    // StreamEditor::deserializeFrom: xorl %edx,%edx before Renderer::deserialize).
    // Must be called AFTER setInputDataStream(), BEFORE render().
    if (lris_path) {
        auto lris_stream = std::make_shared<std::ifstream>(lris_path, std::ios::binary);
        if (!lris_stream->is_open()) {
            fprintf(stderr, "ERROR: Cannot open LRIS file: %s\n", lris_path);
            CIAPI::StaticShutdown();
            return 1;
        }
        try {
            renderer.deserialize(lris_stream, static_cast<CIAPI::StateType>(0));
            printf("  LRIS state loaded.\n");
        } catch (const std::exception& e) {
            fprintf(stderr, "WARNING: deserialize() failed: %s\n"
                            "         Continuing without depth state (DNG may be empty).\n",
                    e.what());
        }
    }

    // Apply camera calibration tuning before render (TuningType 0 = default).
    try { CIAPI::ApplyTuning(static_cast<CIAPI::TuningType>(0), renderer); }
    catch (const std::exception& e) {
        fprintf(stderr, "ApplyTuning failed: %s\n", e.what());
        CIAPI::StaticShutdown();
        return 1;
    }
    if (maximum_in_focus_blur_pixels >= 0.0f)
        renderer.setProperty(static_cast<CIAPI::ParamFloat>(19),
                             maximum_in_focus_blur_pixels);
    if (debug_view_id >= 0)
        renderer.setProperty(static_cast<CIAPI::ParamInt>(20), debug_view_id);
    if (!prepare_mode0_rerender) {
        if (dof_f_number > 0.0f)
            renderer.setProperty(static_cast<CIAPI::ParamFloat>(0), dof_f_number);
        if (dof_focus_depth > 0.0f)
            renderer.setProperty(static_cast<CIAPI::ParamFloat>(1), dof_focus_depth);
    }
    if (renderer_mode >= 0 && !prepare_mode0_rerender)
        renderer.setMode(static_cast<CIAPI::RenderingMode>(renderer_mode));

    if (probe_output_level >= 0) {
        CIAPI::ImagePyramid pyramid = renderer.outputBuffer();
        const int levels = pyramid.levelCount();
        if (probe_output_level >= levels) {
            fprintf(stderr, "Invalid pre-render output level: %d (levels=%d)\n",
                    probe_output_level, levels);
            CIAPI::StaticShutdown();
            return 1;
        }
        pyramid.lock();
        CIAPI::ImagePyramid const& readonly_pyramid = pyramid;
        CIAPI::Image const& image = readonly_pyramid[probe_output_level];
        if (image.empty() || !image.data()) {
            fprintf(stderr, "Pre-render output level %d has no allocated data\n",
                    probe_output_level);
            pyramid.unlock();
            CIAPI::StaticShutdown();
            return 1;
        }
        const int x = image.width() / 2;
        const int y = image.height() / 2;
        auto* address = static_cast<unsigned char*>(image.data())
                      + static_cast<size_t>(y) * image.stride()
                      + static_cast<size_t>(x) * 4;
        printf("OUTPUT_PROBE_TARGET level=%d x=%d y=%d address=%p\n",
               probe_output_level, x, y, address);
        lri_probe_output_write_target(address, probe_output_level, x, y);
        pyramid.unlock();
    }

    // Submit the requested render schedule.
    int w = 0, h = 0;
    CIAPI::ROI roi = {0, 0, 65536, 65536};
    auto request_render = [&]() {
        if (!gui_level_sweep) {
            renderer.render(1, roi, static_cast<CIAPI::RenderType>(render_type), sync_render);
            return;
        }
        CIAPI::ImagePyramid pyramid = renderer.outputBuffer();
        for (int level = pyramid.levelCount() - 1; level >= 0; --level)
            renderer.render(level, roi, static_cast<CIAPI::RenderType>(render_type), sync_render);
    };
    try { request_render(); }
    catch (const std::exception& e) {
        fprintf(stderr, "render() failed: %s\n", e.what());
        CIAPI::StaticShutdown();
        return 1;
    }

    if (prepare_mode0_rerender) {
        if (dof_focus_center) {
            const CIAPI::Point<float> center = {0.5f, 0.5f};
            dof_focus_depth = depth_editor->getDepthAtPoint(center);
            printf("DOF_CENTER_FOCUS_DEPTH value=%.9g\n", dof_focus_depth);
        }
        if (dof_f_number > 0.0f)
            renderer.setProperty(static_cast<CIAPI::ParamFloat>(0), dof_f_number);
        if (dof_focus_depth > 0.0f)
            renderer.setProperty(static_cast<CIAPI::ParamFloat>(1), dof_focus_depth);
        renderer.setMode(static_cast<CIAPI::RenderingMode>(renderer_mode));
        if (quick_select_center) {
            CIAPI::QuickSelectDepthEditingParams selection = {
                {{0.49f, 0.5f}, {0.51f, 0.5f}},
                0.02f,
                true,
                {0, 0, 5216, 3912},
                1,
            };
            depth_editor->addQuickSelectStrokes(selection);
        }
        try { request_render(); }
        catch (const std::exception& e) {
            fprintf(stderr, "prepared rerender() failed: %s\n", e.what());
            CIAPI::StaticShutdown();
            return 1;
        }
    }

    if (brush_edit_rerender) {
        const CIAPI::Point<float> center = {0.5f, 0.5f};
        CIAPI::BrushDepthEditingParams edit = {
            {{0.49f, 0.5f}, {0.51f, 0.5f}},
            0.02f,
            depth_editor->getDepthAtPoint(center) + 100.0f,
            false,
        };
        depth_editor->pushBrushDepthEdit(edit);
        request_render();
    }

    if (inspect_output_pyramid || dump_output_path) {
        printf("OUTPUT_UPDATE_COUNT count=%d\n",
               output_update_count.load(std::memory_order_relaxed));
        CIAPI::ImagePyramid pyramid = renderer.outputBuffer();
        const int levels = pyramid.levelCount();
        printf("OUTPUT_PYRAMID levels=%d\n", levels);
        pyramid.lock();
        const CIAPI::ImagePyramid& readonly_pyramid = pyramid;
        for (int level = 0; level < levels; ++level) {
            try {
                CIAPI::Image const& image = readonly_pyramid[level];
                printf("OUTPUT_PYRAMID_LEVEL level=%d empty=%d width=%d height=%d "
                       "stride=%d plane_stride=%d pixel_format=%d data=%p\n",
                       level, image.empty() ? 1 : 0, image.width(), image.height(),
                       image.stride(), image.planeStride(),
                       static_cast<int>(image.pixelFormat()), image.data());
            } catch (const std::exception& e) {
                printf("OUTPUT_PYRAMID_LEVEL level=%d error=%s\n", level, e.what());
            }
        }
        if (dump_output_path) {
            if (dump_output_level < 0 || dump_output_level >= levels) {
                fprintf(stderr, "Invalid output-pyramid dump level: %d\n", dump_output_level);
                pyramid.unlock();
                CIAPI::StaticShutdown();
                return 1;
            }
            CIAPI::Image const& image = readonly_pyramid[dump_output_level];
            write_raw(dump_output_path, image.width(), image.height(), image.stride(),
                      image.data(), static_cast<int>(image.pixelFormat()));
        }
        pyramid.unlock();
    }

    if (render_only) {
        printf("  render-only request completed.\n");
        CIAPI::StaticShutdown();
        return 0;
    }

    // SPIKE RESULT (2026-04-11): writeImage respects Point<int> as the exact output resolution.
    // Passing {10432,7824} (confirmed from Export DNG archive: L16 full-res fused output) produces
    // a 217MB TIFF at full resolution, matching Lumen GUI export.
    // Passing {65536,65536} → SIGBUS (no auto-clip — renderer allocates exactly that much).
    // Passing {4160,3120} (DirectRenderer preview) → 30MB downscaled output.
    //
    // L16 native full-res is always 10432×7824 (13-camera fused, 81.6 MP).
    // This is hardcoded because no post-render API yields pixel dimensions:
    //   - outputBuffer()[0] throws "invalid pyramid level selected!" in export mode
    //   - transform()->aspectRatio() returns reduced aspect ratio (4:3), not pixel dims
    //   - LRI file protobuf parsing would work but is out of scope for this spike
    //
    // TODO: parse LRI protobuf header to get native dims for non-L16 Light cameras.
    w = output_width; h = output_height;
    fprintf(stderr, "Using L16 full-res dimensions: %dx%d\n", w, h);

    if (w <= 0 || h <= 0) {
        fprintf(stderr, "Cannot determine output dimensions\n");
        CIAPI::StaticShutdown();
        return 1;
    }

    auto out_stream = std::make_shared<std::ofstream>(output_path, std::ios::binary);
    if (!out_stream->is_open()) {
        fprintf(stderr, "Cannot open for writing: %s\n", output_path);
        CIAPI::StaticShutdown();
        return 1;
    }

    // Point<int> = {width, height} (confirmed from Lumen's SizeSpec::size() in disassembly).
    CIAPI::Point<int> outsize = {w, h};
    try {
        renderer.writeImage(out_stream, outsize,
            static_cast<CIAPI::ExportImageFormat>(export_fmt),
            [](int pct) {
                printf("  %3d%%\r", pct);
                fflush(stdout);
            });
    } catch (const std::exception& e) {
        fprintf(stderr, "\nwriteImage() failed: %s\n", e.what());
        CIAPI::StaticShutdown();
        return 1;
    }

    out_stream->flush();
    if (!out_stream->good()) {
        fprintf(stderr, "\nStream write error on: %s\n", output_path);
        CIAPI::StaticShutdown();
        return 1;
    }

    printf("\n  Written: %s (%dx%d)\n", output_path, w, h);

    // ── Optionally serialize render state to .lris ──────────────
    // Used for QA investigation: captures freshly computed depth when
    // rendered without a .lris sidecar.
    if (write_lris_path) {
        auto lris_out = std::make_shared<std::ofstream>(write_lris_path, std::ios::binary);
        if (!lris_out->is_open()) {
            fprintf(stderr, "WARNING: Cannot open for writing: %s\n", write_lris_path);
        } else {
            try {
                renderer.serialize(lris_out, static_cast<CIAPI::StateType>(0));
                lris_out->flush();
                if (lris_out->good())
                    printf("  LRIS written: %s\n", write_lris_path);
                else
                    fprintf(stderr, "WARNING: LRIS stream write error\n");
            } catch (const std::exception& e) {
                fprintf(stderr, "WARNING: serialize() failed: %s\n", e.what());
            }
        }
    }

    CIAPI::StaticShutdown();
    return 0;
}
