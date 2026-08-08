#include <mach-o/dyld.h>
#include <math.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

typedef struct {
    int32_t origin_x;
    int32_t origin_y;
    int32_t limit_x;
    int32_t limit_y;
    int32_t width;
    int32_t height;
    int32_t stride;
    int32_t reserved;
    void *data;
} Image;

typedef void *(*range_fn)(float *, void *, float);

extern void range_hook_shim(void);
extern void post_overlay_hook_shim(void);

typedef struct {
    float *pre_color;
    float *depth;
    Image *output;
    int width;
    int height;
    float lower;
    float upper;
    float color[4];
    float max_blur;
    int active;
} ThreadCapture;

static uintptr_t libcp_base;
static void *range_trampoline;
static _Thread_local ThreadCapture capture;
static pthread_mutex_t report_lock = PTHREAD_MUTEX_INITIALIZER;
static uint64_t range_calls;
static uint64_t overlay_calls;
static uint64_t pixels;
static uint64_t outside_pixels;
static uint64_t exact_lanes;
static uint64_t total_lanes;
static float maximum_error;
static uint64_t descriptor_mismatches;
static uint64_t parameter_mismatches;
static uint32_t lower_bits;
static uint32_t upper_bits;
static uint32_t color_bits[4];
static uint32_t max_blur_bits;

static uint32_t float_bits(float value) {
    uint32_t bits;
    memcpy(&bits, &value, sizeof(bits));
    return bits;
}

static uintptr_t find_libcp_base(void) {
    for (uint32_t i = 0; i < _dyld_image_count(); ++i) {
        const char *name = _dyld_get_image_name(i);
        if (name != NULL && strstr(name, "/libcp.dylib") != NULL)
            return (uintptr_t)_dyld_get_image_header(i);
    }
    return 0;
}

static void write_absolute_jump(uint8_t *destination, const void *target) {
    destination[0] = 0x48;
    destination[1] = 0xb8;
    uintptr_t address = (uintptr_t)target;
    memcpy(destination + 2, &address, sizeof(address));
    destination[10] = 0xff;
    destination[11] = 0xe0;
}

static void write_absolute_call(uint8_t *destination, const void *target) {
    destination[0] = 0x48;
    destination[1] = 0xb8;
    uintptr_t address = (uintptr_t)target;
    memcpy(destination + 2, &address, sizeof(address));
    destination[10] = 0xff;
    destination[11] = 0xd0;
}

static void make_writable(void *address) {
    long page_size = sysconf(_SC_PAGESIZE);
    uintptr_t page = (uintptr_t)address & ~((uintptr_t)page_size - 1);
    if (mprotect((void *)page, (size_t)page_size,
                 PROT_READ | PROT_WRITE | PROT_EXEC) != 0)
        abort();
}

static void *install_hook(uintptr_t va, size_t copied, const void *hook) {
    uint8_t *entry = (uint8_t *)(libcp_base + va);
    uint8_t *trampoline = mmap(NULL, 4096, PROT_READ | PROT_WRITE | PROT_EXEC,
                               MAP_PRIVATE | MAP_ANON, -1, 0);
    if (trampoline == MAP_FAILED) return NULL;
    memcpy(trampoline, entry, copied);
    write_absolute_jump(trampoline + copied, entry + copied);
    make_writable(entry);
    write_absolute_jump(entry, hook);
    memset(entry + 12, 0x90, copied - 12);
    __builtin___clear_cache((char *)entry, (char *)entry + copied);
    return trampoline;
}

static int valid_image(const Image *image) {
    return image != NULL && image->data != NULL && image->width > 0 &&
           image->height > 0 && image->stride >= image->width;
}

static void reset_capture(void) {
    free(capture.pre_color);
    free(capture.depth);
    memset(&capture, 0, sizeof(capture));
}

__attribute__((noinline))
void *range_hook_c(float *output, void *cache, Image *color_image,
                   void *renderer, void *parent_frame, float max_blur) {
    uintptr_t return_va = (uintptr_t)__builtin_return_address(0) - libcp_base;
    void *result = ((range_fn)range_trampoline)(output, cache, max_blur);
    if (return_va != 0x3bbe28) return result;

    Image *depth_image = (Image *)((uint8_t *)parent_frame - 0x290);
    reset_capture();
    if (!valid_image(color_image) || !valid_image(depth_image) ||
        color_image->width != depth_image->width ||
        color_image->height != depth_image->height)
        return result;

    size_t count = (size_t)color_image->width * (size_t)color_image->height;
    capture.pre_color = malloc(count * 4 * sizeof(float));
    capture.depth = malloc(count * sizeof(float));
    if (capture.pre_color == NULL || capture.depth == NULL) abort();
    for (int y = 0; y < color_image->height; ++y) {
        memcpy(capture.pre_color + (size_t)y * (size_t)color_image->width * 4,
               (const float *)color_image->data +
                   (size_t)y * (size_t)color_image->stride * 4,
               (size_t)color_image->width * 4 * sizeof(float));
        memcpy(capture.depth + (size_t)y * (size_t)depth_image->width,
               (const float *)depth_image->data +
                   (size_t)y * (size_t)depth_image->stride,
               (size_t)depth_image->width * sizeof(float));
    }
    capture.output = color_image;
    capture.width = color_image->width;
    capture.height = color_image->height;
    capture.lower = output[0];
    capture.upper = output[1];
    memcpy(capture.color, (uint8_t *)renderer + 0x8d0, 4 * sizeof(float));
    capture.max_blur = *(float *)((uint8_t *)renderer + 0x8e0);
    capture.active = 1;

    pthread_mutex_lock(&report_lock);
    ++range_calls;
    uint32_t observed[7] = {
        float_bits(capture.lower), float_bits(capture.upper),
        float_bits(capture.color[0]), float_bits(capture.color[1]),
        float_bits(capture.color[2]), float_bits(capture.color[3]),
        float_bits(capture.max_blur),
    };
    uint32_t prior[7] = {lower_bits, upper_bits, color_bits[0], color_bits[1],
                         color_bits[2], color_bits[3], max_blur_bits};
    if (range_calls > 1 && memcmp(observed, prior, sizeof(observed)) != 0)
        ++parameter_mismatches;
    lower_bits = observed[0];
    upper_bits = observed[1];
    memcpy(color_bits, observed + 2, sizeof(color_bits));
    max_blur_bits = observed[6];
    pthread_mutex_unlock(&report_lock);
    return result;
}

__attribute__((noinline))
void post_overlay_hook_c(Image *color_image, void *parent_frame) {
    Image *depth_descriptor = (Image *)((uint8_t *)parent_frame - 0x290);

    uint64_t local_pixels = 0;
    uint64_t local_outside = 0;
    uint64_t local_exact = 0;
    float local_maximum = 0;
    int mismatch = 0;
    if (!capture.active || color_image != capture.output ||
        !valid_image(color_image) || color_image->width != capture.width ||
        color_image->height != capture.height) {
        mismatch = 1;
    } else {
        for (int y = 0; y < capture.height; ++y) {
            const float *dst = (const float *)color_image->data +
                               (size_t)y * (size_t)color_image->stride * 4;
            for (int x = 0; x < capture.width; ++x) {
                size_t index = (size_t)y * (size_t)capture.width + (size_t)x;
                float depth = capture.depth[index];
                float alpha = (depth < capture.lower || capture.upper < depth)
                                  ? capture.color[3] : 0.0f;
                if (alpha != 0.0f) ++local_outside;
                for (int lane = 0; lane < 4; ++lane) {
                    float tint_value = lane == 3 ? 1.0f : capture.color[lane];
                    volatile float inverse = 1.0f - alpha;
                    volatile float base = inverse * capture.pre_color[4 * index + lane];
                    volatile float tint = alpha * tint_value;
                    float expected = base + tint;
                    float actual = dst[4 * x + lane];
                    float error = fabsf(actual - expected);
                    if (float_bits(actual) == float_bits(expected)) ++local_exact;
                    if (error > local_maximum) local_maximum = error;
                }
                ++local_pixels;
            }
        }
    }

    pthread_mutex_lock(&report_lock);
    ++overlay_calls;
    pixels += local_pixels;
    outside_pixels += local_outside;
    exact_lanes += local_exact;
    total_lanes += local_pixels * 4;
    if (local_maximum > maximum_error) maximum_error = local_maximum;
    descriptor_mismatches += mismatch;
    pthread_mutex_unlock(&report_lock);
    reset_capture();

    ((void (*)(Image *))(libcp_base + 0xf4e0))(depth_descriptor);
}

__attribute__((constructor))
static void install_refocus_point_hooks(void) {
    libcp_base = find_libcp_base();
    if (libcp_base == 0) return;
    range_trampoline = install_hook(0x3f08c0, 16,
                                    (const void *)&range_hook_shim);
    uint8_t *callsite = (uint8_t *)(libcp_base + 0x3bbf06);
    make_writable(callsite);
    write_absolute_call(callsite, (const void *)&post_overlay_hook_shim);
    __builtin___clear_cache((char *)callsite, (char *)callsite + 12);
}

__attribute__((destructor))
static void write_report(void) {
    const char *path = getenv("L16_REFOCUS_POINT_OUT");
    if (path == NULL) return;
    FILE *output = fopen(path, "w");
    if (output == NULL) return;
    fprintf(output,
            "{\n"
            "  \"range_calls\": %llu,\n"
            "  \"overlay_calls\": %llu,\n"
            "  \"pixels\": %llu,\n"
            "  \"outside_pixels\": %llu,\n"
            "  \"exact_lanes\": %llu,\n"
            "  \"total_lanes\": %llu,\n"
            "  \"max_abs\": %.9g,\n"
            "  \"descriptor_mismatches\": %llu,\n"
            "  \"parameter_mismatches\": %llu,\n"
            "  \"lower_bits\": \"%08x\",\n"
            "  \"upper_bits\": \"%08x\",\n"
            "  \"color_bits\": [\"%08x\",\"%08x\",\"%08x\",\"%08x\"],\n"
            "  \"max_blur_bits\": \"%08x\"\n"
            "}\n",
            (unsigned long long)range_calls,
            (unsigned long long)overlay_calls,
            (unsigned long long)pixels,
            (unsigned long long)outside_pixels,
            (unsigned long long)exact_lanes,
            (unsigned long long)total_lanes, maximum_error,
            (unsigned long long)descriptor_mismatches,
            (unsigned long long)parameter_mismatches,
            lower_bits, upper_bits, color_bits[0], color_bits[1],
            color_bits[2], color_bits[3], max_blur_bits);
    fclose(output);
}
