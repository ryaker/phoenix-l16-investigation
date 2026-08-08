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

typedef void *(*image_unary_fn)(Image *, const Image *);
typedef void *(*generated_fn)(Image *, const void *);

static uintptr_t libcp_base;
static void *scalar_trampoline;
static void *mask_trampoline;
static void *blend_trampoline;
static uintptr_t selected_converter_va;
static pthread_mutex_t report_lock = PTHREAD_MUTEX_INITIALIZER;

static uint64_t scalar_calls;
static uint64_t scalar_pixels;
static uint64_t scalar_exact[4];
static float scalar_max_abs[4];
static uint64_t scalar_rec601_exact;
static float scalar_rec601_max_abs;
static uint64_t mask_calls;
static uint64_t mask_pixels;
static uint64_t mask_exact;
static float mask_max_abs;
static uint64_t mask_parameter_mismatch;
static uint32_t focus_bits;
static uint32_t q_bits;
static uint32_t one_bits;
static uint32_t scale_bits;
static uint64_t blend_calls;
static uint64_t blend_pixels;
static uint64_t blend_exact_lanes;
static uint64_t blend_total_lanes;
static float blend_max_abs;

enum { SAMPLE_LIMIT = 32 };
static uint32_t sample_count;
static float sample_rgba[SAMPLE_LIMIT][4];
static float sample_scalar[SAMPLE_LIMIT];
static uint32_t mask_sample_count;
static float sample_depth[SAMPLE_LIMIT];
static float sample_mask[SAMPLE_LIMIT];
static uint32_t blend_sample_count;
static float sample_blend_gray[SAMPLE_LIMIT];
static float sample_blend_mask[SAMPLE_LIMIT];
static float sample_blend[SAMPLE_LIMIT][4];

static uint32_t float_bits(float value) {
    uint32_t bits;
    memcpy(&bits, &value, sizeof(bits));
    return bits;
}

static float bits_float(uint32_t bits) {
    float value;
    memcpy(&value, &bits, sizeof(value));
    return value;
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

static void *install_hook(uintptr_t va, size_t copied, const void *hook) {
    uint8_t *entry = (uint8_t *)(libcp_base + va);
    uint8_t *trampoline = mmap(NULL, 4096, PROT_READ | PROT_WRITE | PROT_EXEC,
                               MAP_PRIVATE | MAP_ANON, -1, 0);
    if (trampoline == MAP_FAILED) return NULL;
    memcpy(trampoline, entry, copied);
    write_absolute_jump(trampoline + copied, entry + copied);
    long page_size = sysconf(_SC_PAGESIZE);
    uintptr_t page = (uintptr_t)entry & ~((uintptr_t)page_size - 1);
    if (mprotect((void *)page, (size_t)page_size,
                 PROT_READ | PROT_WRITE | PROT_EXEC) != 0) return NULL;
    write_absolute_jump(entry, hook);
    memset(entry + 12, 0x90, copied - 12);
    __builtin___clear_cache((char *)entry, (char *)entry + copied);
    return trampoline;
}

static int valid_image(const Image *image, int channels) {
    return image != NULL && image->data != NULL && image->width > 0 &&
           image->height > 0 && image->stride >= image->width && channels > 0;
}

/* This is the scalar SSE lane at 0x3c13e0, including its integer bit trick. */
static float refocus_fast_mask(float depth, float focus, float q,
                               float one, float scale) {
    volatile float delta = depth - focus;
    volatile float squared = delta * delta;
    volatile float x0 = -squared * q;
    float x = x0;
    if (x > 128.0f) x = 128.0f;
    if (x < -126.0f) x = -126.0f;
    int32_t truncated = (int32_t)x;
    int32_t exponent = truncated + (x < 0.0f ? -1 : 0);
    volatile float fraction = x - (float)exponent;
    volatile float p0 = fraction * 0.07802452147006989f;
    volatile float p1 = p0 + 0.22606715559959412f;
    volatile float p2 = p1 * fraction;
    volatile float p3 = p2 + 0.69583356380462646f;
    volatile float p4 = p3 * fraction;
    volatile float polynomial = p4 + 0.99992519617080688f;
    uint32_t exp2_bits = float_bits(polynomial) +
                         ((uint32_t)exponent << 23);
    volatile float exp2_value = bits_float(exp2_bits);
    volatile float complement = one - exp2_value;
    return complement * scale;
}

static float rec601_scalar(const float *rgba) {
    volatile float red = rgba[0] * bits_float(UINT32_C(0x3e991687));
    volatile float green = rgba[1] * bits_float(UINT32_C(0x3f1645a2));
    volatile float red_green = green + red;
    volatile float blue = rgba[2] * bits_float(UINT32_C(0x3de978d5));
    return blue + red_green;
}

__attribute__((noinline))
static void *scalar_hook(Image *output, const Image *input) {
    uintptr_t return_va = (uintptr_t)__builtin_return_address(0) - libcp_base;
    void *result = ((image_unary_fn)scalar_trampoline)(output, input);
    if (return_va != 0x3bbcad) return result;
    if (!valid_image(output, 1) || !valid_image(input, 4) ||
        output->width != input->width || output->height != input->height)
        return result;

    uint64_t pixels = 0;
    uint64_t exact[4] = {0, 0, 0, 0};
    float maximum[4] = {0, 0, 0, 0};
    uint64_t rec601_exact = 0;
    float rec601_maximum = 0;
    float local_rgba[SAMPLE_LIMIT][4];
    float local_scalar[SAMPLE_LIMIT];
    uint32_t local_count = 0;
    for (int y = 0; y < output->height; ++y) {
        const float *src = (const float *)input->data +
                           (size_t)y * (size_t)input->stride * 4;
        const float *dst = (const float *)output->data +
                           (size_t)y * (size_t)output->stride;
        for (int x = 0; x < output->width; ++x) {
            float value = dst[x];
            for (int lane = 0; lane < 4; ++lane) {
                float candidate = src[4 * x + lane];
                float error = fabsf(value - candidate);
                if (float_bits(value) == float_bits(candidate)) ++exact[lane];
                if (error > maximum[lane]) maximum[lane] = error;
            }
            float expected = rec601_scalar(src + 4 * x);
            float rec601_error = fabsf(value - expected);
            if (float_bits(value) == float_bits(expected)) ++rec601_exact;
            if (rec601_error > rec601_maximum) rec601_maximum = rec601_error;
            if (local_count < SAMPLE_LIMIT) {
                memcpy(local_rgba[local_count], src + 4 * x, 4 * sizeof(float));
                local_scalar[local_count] = value;
                ++local_count;
            }
            ++pixels;
        }
    }

    pthread_mutex_lock(&report_lock);
    ++scalar_calls;
    scalar_pixels += pixels;
    for (int lane = 0; lane < 4; ++lane) {
        scalar_exact[lane] += exact[lane];
        if (maximum[lane] > scalar_max_abs[lane]) scalar_max_abs[lane] = maximum[lane];
    }
    scalar_rec601_exact += rec601_exact;
    if (rec601_maximum > scalar_rec601_max_abs)
        scalar_rec601_max_abs = rec601_maximum;
    for (uint32_t i = 0; i < local_count && sample_count < SAMPLE_LIMIT; ++i) {
        memcpy(sample_rgba[sample_count], local_rgba[i], 4 * sizeof(float));
        sample_scalar[sample_count] = local_scalar[i];
        ++sample_count;
    }
    pthread_mutex_unlock(&report_lock);
    return result;
}

__attribute__((noinline))
static void *mask_hook(Image *output, const void *configuration) {
    const uint8_t *root = (const uint8_t *)configuration;
    const uint8_t *n1 = *(const uint8_t *const *)root;
    const uint8_t *n2 = *(const uint8_t *const *)n1;
    const uint8_t *n3 = *(const uint8_t *const *)n2;
    const uint8_t *n4 = *(const uint8_t *const *)n3;
    const uint8_t *n5 = *(const uint8_t *const *)n4;
    const uint8_t *n6 = *(const uint8_t *const *)n5;
    const Image *depth = *(const Image *const *)n6;
    float focus = *(const float *)(n6 + 8);
    float q = *(const float *)(n3 + 8);
    float one = *(const float *)(n1 + 8);
    float scale = *(const float *)(root + 8);
    void *result = ((generated_fn)mask_trampoline)(output, configuration);
    if (!valid_image(output, 1) || !valid_image(depth, 1) ||
        output->width != depth->width || output->height != depth->height)
        return result;

    uint64_t pixels = 0;
    uint64_t exact = 0;
    float maximum = 0;
    pthread_mutex_lock(&report_lock);
    if (mask_calls != 0 &&
        (focus_bits != float_bits(focus) || q_bits != float_bits(q) ||
         one_bits != float_bits(one) || scale_bits != float_bits(scale)))
        ++mask_parameter_mismatch;
    focus_bits = float_bits(focus);
    q_bits = float_bits(q);
    one_bits = float_bits(one);
    scale_bits = float_bits(scale);
    pthread_mutex_unlock(&report_lock);

    for (int y = 0; y < output->height; ++y) {
        const float *src = (const float *)depth->data +
                           (size_t)y * (size_t)depth->stride;
        const float *dst = (const float *)output->data +
                           (size_t)y * (size_t)output->stride;
        for (int x = 0; x < output->width; ++x) {
            float expected = refocus_fast_mask(src[x], focus, q, one, scale);
            float error = fabsf(dst[x] - expected);
            if (float_bits(dst[x]) == float_bits(expected)) ++exact;
            if (error > maximum) maximum = error;
            ++pixels;
        }
    }

    pthread_mutex_lock(&report_lock);
    ++mask_calls;
    mask_pixels += pixels;
    mask_exact += exact;
    if (maximum > mask_max_abs) mask_max_abs = maximum;
    const float *depth_row = (const float *)depth->data;
    const float *mask_row = (const float *)output->data;
    while (mask_sample_count < SAMPLE_LIMIT &&
           mask_sample_count < (uint32_t)output->width) {
        sample_depth[mask_sample_count] = depth_row[mask_sample_count];
        sample_mask[mask_sample_count] = mask_row[mask_sample_count];
        ++mask_sample_count;
    }
    pthread_mutex_unlock(&report_lock);
    return result;
}

__attribute__((noinline))
static void *blend_hook(Image *output, const void *configuration) {
    const uint8_t *root = (const uint8_t *)configuration;
    const uint8_t *left = *(const uint8_t *const *)root;
    const uint8_t *right = *(const uint8_t *const *)(root + 8);
    const Image *gray = *(const Image *const *)left;
    const uint8_t *mask_pair = *(const uint8_t *const *)(left + 8);
    const Image *mask = *(const Image *const *)mask_pair;
    float one = *(const float *)(mask_pair + 8);
    const Image *right_mask = *(const Image *const *)right;
    float color[4];
    memcpy(color, right + 0x10, sizeof(color));
    void *result = ((generated_fn)blend_trampoline)(output, configuration);
    if (!valid_image(output, 4) || !valid_image(gray, 1) ||
        !valid_image(mask, 1) || right_mask != mask ||
        output->width != gray->width || output->height != gray->height)
        return result;

    uint64_t pixels = 0;
    uint64_t exact = 0;
    float maximum = 0;
    for (int y = 0; y < output->height; ++y) {
        const float *g = (const float *)gray->data +
                         (size_t)y * (size_t)gray->stride;
        const float *m = (const float *)mask->data +
                         (size_t)y * (size_t)mask->stride;
        const float *dst = (const float *)output->data +
                           (size_t)y * (size_t)output->stride * 4;
        for (int x = 0; x < output->width; ++x) {
            for (int lane = 0; lane < 4; ++lane) {
                volatile float base = (one - m[x]) * g[x];
                volatile float tint = m[x] * color[lane];
                float expected = base + tint;
                float error = fabsf(dst[4 * x + lane] - expected);
                if (float_bits(dst[4 * x + lane]) == float_bits(expected)) ++exact;
                if (error > maximum) maximum = error;
            }
            ++pixels;
        }
    }

    pthread_mutex_lock(&report_lock);
    ++blend_calls;
    blend_pixels += pixels;
    blend_exact_lanes += exact;
    blend_total_lanes += pixels * 4;
    if (maximum > blend_max_abs) blend_max_abs = maximum;
    const float *gray_row = (const float *)gray->data;
    const float *mask_row = (const float *)mask->data;
    const float *output_row = (const float *)output->data;
    while (blend_sample_count < SAMPLE_LIMIT &&
           blend_sample_count < (uint32_t)output->width) {
        sample_blend_gray[blend_sample_count] = gray_row[blend_sample_count];
        sample_blend_mask[blend_sample_count] = mask_row[blend_sample_count];
        memcpy(sample_blend[blend_sample_count],
               output_row + 4 * blend_sample_count, 4 * sizeof(float));
        ++blend_sample_count;
    }
    pthread_mutex_unlock(&report_lock);
    return result;
}

__attribute__((constructor))
static void install_refocus_hooks(void) {
    libcp_base = find_libcp_base();
    if (libcp_base == 0) return;
    void *(*select_converter)(int, int) =
        (void *(*)(int, int))(libcp_base + 0x1cd40);
    selected_converter_va = (uintptr_t)select_converter(7, 16) - libcp_base;
    scalar_trampoline = install_hook(0x2e7710, 14, (const void *)&scalar_hook);
    mask_trampoline = install_hook(0x3c1280, 17, (const void *)&mask_hook);
    blend_trampoline = install_hook(0x3c0fc0, 17, (const void *)&blend_hook);
}

__attribute__((destructor))
static void write_report(void) {
    const char *path = getenv("L16_REFOCUS_SLIDER_OUT");
    if (path == NULL) return;
    FILE *output = fopen(path, "w");
    if (output == NULL) return;
    fprintf(output,
            "{\n"
            "  \"scalar\": {\"calls\":%llu,\"pixels\":%llu,"
            "\"exact_rgba\":[%llu,%llu,%llu,%llu],"
            "\"max_abs_rgba\":[%.9g,%.9g,%.9g,%.9g],"
            "\"rec601_exact\":%llu,\"rec601_max_abs\":%.9g,"
            "\"selected_converter_va\":\"0x%llx\"},\n"
            "  \"mask\": {\"calls\":%llu,\"pixels\":%llu,"
            "\"exact\":%llu,\"max_abs\":%.9g,\"parameter_mismatch\":%llu,"
            "\"focus_bits\":\"%08x\",\"q_bits\":\"%08x\","
            "\"one_bits\":\"%08x\",\"scale_bits\":\"%08x\"},\n"
            "  \"blend\": {\"calls\":%llu,\"pixels\":%llu,"
            "\"exact_lanes\":%llu,\"total_lanes\":%llu,\"max_abs\":%.9g},\n"
            "  \"samples\": [\n",
            (unsigned long long)scalar_calls,
            (unsigned long long)scalar_pixels,
            (unsigned long long)scalar_exact[0],
            (unsigned long long)scalar_exact[1],
            (unsigned long long)scalar_exact[2],
            (unsigned long long)scalar_exact[3],
            scalar_max_abs[0], scalar_max_abs[1], scalar_max_abs[2], scalar_max_abs[3],
            (unsigned long long)scalar_rec601_exact, scalar_rec601_max_abs,
            (unsigned long long)selected_converter_va,
            (unsigned long long)mask_calls,
            (unsigned long long)mask_pixels,
            (unsigned long long)mask_exact, mask_max_abs,
            (unsigned long long)mask_parameter_mismatch,
            focus_bits, q_bits, one_bits, scale_bits,
            (unsigned long long)blend_calls,
            (unsigned long long)blend_pixels,
            (unsigned long long)blend_exact_lanes,
            (unsigned long long)blend_total_lanes, blend_max_abs);
    for (uint32_t i = 0; i < sample_count; ++i) {
        fprintf(output,
                "    {\"kind\":\"scalar\",\"rgba\":[%.9g,%.9g,%.9g,%.9g],"
                "\"scalar\":%.9g},\n",
                sample_rgba[i][0], sample_rgba[i][1], sample_rgba[i][2],
                sample_rgba[i][3], sample_scalar[i]);
    }
    for (uint32_t i = 0; i < mask_sample_count; ++i) {
        fprintf(output,
                "    {\"kind\":\"mask\",\"depth\":%.9g,\"mask\":%.9g},\n",
                sample_depth[i], sample_mask[i]);
    }
    for (uint32_t i = 0; i < blend_sample_count; ++i) {
        fprintf(output,
                "    {\"kind\":\"blend\",\"gray\":%.9g,\"mask\":%.9g,"
                "\"output\":[%.9g,%.9g,%.9g,%.9g]}%s\n",
                sample_blend_gray[i], sample_blend_mask[i],
                sample_blend[i][0], sample_blend[i][1], sample_blend[i][2],
                sample_blend[i][3], i + 1 == blend_sample_count ? "" : ",");
    }
    fprintf(output, "  ]\n}\n");
    fclose(output);
}
