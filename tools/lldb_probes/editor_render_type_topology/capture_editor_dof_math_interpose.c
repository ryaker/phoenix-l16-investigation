#include <mach-o/dyld.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

static uintptr_t libcp_base;
static void *range_trampoline;
static void *radius_trampoline;
static void *tiled_trampoline;
static void *circle_vec_trampoline;
static void *circle_float_trampoline;
static void *layer_records_trampoline;
static void *layer_transition_trampoline;
static void *layer_filter_trampoline;
static void *resample_trampoline;
static void *gaussian_trampoline;

static _Atomic uint64_t range_calls;
static _Atomic uint64_t radius_calls;
static _Atomic uint64_t tiled_calls;
static _Atomic uint64_t circle_vec_calls;
static _Atomic uint64_t circle_float_calls;
static _Atomic int radius_min;
static _Atomic int radius_max;
static _Atomic int circle_vec_min;
static _Atomic int circle_vec_max;
static _Atomic int circle_float_min;
static _Atomic int circle_float_max;
static _Atomic uint64_t layer_records_calls;
static _Atomic uint64_t layer_transition_calls;
static _Atomic uint64_t layer_transition_less_calls;
static _Atomic uint64_t layer_transition_equal_calls;
static _Atomic uint64_t layer_transition_greater_calls;
static _Atomic uint64_t layer_filter_calls;
static _Atomic uint64_t layer_filter_copy_calls;
static _Atomic uint64_t layer_filter_small_calls;
static _Atomic uint64_t layer_filter_large_calls;
static _Atomic uint64_t layer_filter_resample_calls;
static _Atomic uint64_t layer_filter_equal_rect_calls;
static _Atomic uint64_t layer_filter_distinct_rect_calls;

#define LAYER_FILTER_SAMPLE_LIMIT 128
#define LAYER_RESAMPLE_SAMPLE_LIMIT 256

struct layer_filter_sample {
    int input_width;
    int input_height;
    int diameter;
    int depth_type;
    int first_rect[4];
    int second_rect[4];
    int branch;
};

struct layer_resample_sample {
    int output_width;
    int output_height;
    int input_width;
    int input_height;
    uint64_t offset_bits[2];
    uint64_t scale_bits[2];
    int diameter;
    int depth_type;
    int first_rect[4];
};

static struct layer_filter_sample
    layer_filter_samples[LAYER_FILTER_SAMPLE_LIMIT];
static struct layer_resample_sample
    layer_resample_samples[LAYER_RESAMPLE_SAMPLE_LIMIT];
static _Atomic unsigned layer_filter_sample_count;
static _Atomic unsigned layer_resample_sample_count;
static _Thread_local unsigned layer_filter_depth;
static _Thread_local int layer_filter_diameter;
static _Thread_local int layer_filter_depth_type;
static _Thread_local int layer_filter_first_rect[4];
static _Atomic unsigned gaussian5_captured;
static uint32_t gaussian5_bits[5];

#define LAYER_RECORD_LIMIT 256
#define LAYER_RADIUS_LIMIT 1024
#define LAYER_TABLE_LIMIT 32
#define LAYER_TABLE_RECORD_LIMIT 32

struct layer_record_sample {
    uint32_t lower_bits;
    uint32_t upper_bits;
    int radius;
    uint64_t primary_count;
    uint64_t secondary_count;
};

static struct layer_record_sample layer_record_samples[LAYER_RECORD_LIMIT];
static _Atomic uint64_t layer_radius_incidence[LAYER_RADIUS_LIMIT + 1];
static _Atomic int layer_capture_state;
static unsigned layer_record_sample_count;
static uint32_t layer_context_a0_bits[4];
static uint32_t layer_context_range_bits[2];
static int layer_context_depth_type;
static int layer_context_b0;
static unsigned char layer_context_b4;
static unsigned char layer_context_b5;

struct layer_table_sample {
    uint32_t range_bits[2];
    int depth_type;
    int b0;
    unsigned char b4;
    unsigned char b5;
    int primary_width;
    int primary_height;
    int secondary_width;
    int secondary_height;
    unsigned char secondary_present;
    unsigned record_count;
    struct layer_record_sample records[LAYER_TABLE_RECORD_LIMIT];
};

static struct layer_table_sample layer_table_samples[LAYER_TABLE_LIMIT];
static unsigned layer_table_sample_count;
static atomic_flag layer_table_lock = ATOMIC_FLAG_INIT;

#define LAYER_TRANSITION_SAMPLE_LIMIT 64

struct layer_transition_sample {
    uint32_t source_upper_bits;
    uint32_t boundary_upper_bits;
    int source_radius;
    int boundary_radius;
    int b0;
    unsigned char b4;
    unsigned char b5;
    int x;
    int y;
    uint32_t color_bits[3];
    uint32_t depth_bits;
    uint32_t output_bits[4];
};

static struct layer_transition_sample
    layer_transition_samples[LAYER_TRANSITION_SAMPLE_LIMIT];
static _Atomic unsigned layer_transition_sample_count;

static uint32_t range_input[5];
static uint32_t range_output[2];
static uint32_t radius_depth_range[2];
static uint32_t radius_input[4];
static int radius_depth_type;
static int radius_first_result;
static uint32_t tiled_input[4];
static int tiled_first_radius;
static int tiled_first_flag;
static int tiled_first_device;

#define RANGE_SAMPLE_LIMIT 64
#define RADIUS_RESULT_LIMIT 128

struct range_sample {
    uint32_t input[5];
    uint32_t output[2];
};

struct radius_sample {
    uint32_t depth_range[2];
    uint32_t input[4];
    int depth_type;
    int result;
};

static struct range_sample range_samples[RANGE_SAMPLE_LIMIT];
static struct radius_sample radius_result_samples[RADIUS_RESULT_LIMIT + 1];
static _Atomic unsigned range_sample_count;
static _Atomic unsigned char radius_result_seen[RADIUS_RESULT_LIMIT + 1];

typedef void *(*range_fn)(void *, float, float, float, float, float);
typedef int (*radius_fn)(const float *, int, float, float, float, float);
typedef void *(*tiled_fn)(void *, void *, int, float, float, float, float,
                          unsigned char, int);
typedef void (*circle_fn)(void *, const void *, int);
typedef void *(*layer_records_fn)(void *, void *);
typedef void (*layer_transition_fn)(void *, void *, const void *, const void *);
typedef void (*layer_filter_fn)(void *, void *, const int *, const int *, int, int);
typedef void (*resample_fn)(void *, void *, const double *, const double *);
typedef void *(*gaussian_fn)(void *, int, float, float);

static uint32_t fbits(float value) {
    uint32_t bits;
    memcpy(&bits, &value, sizeof(bits));
    return bits;
}

static uint64_t dbits(double value) {
    uint64_t bits;
    memcpy(&bits, &value, sizeof(bits));
    return bits;
}

__attribute__((noinline))
static void *gaussian_hook(void *output, int count, float sigma, float scale) {
    void *result = ((gaussian_fn)gaussian_trampoline)(
        output, count, sigma, scale);
    if (count == 5 && fbits(sigma) == 0x3f800000 &&
        fbits(scale) == 0x3f800000) {
        unsigned expected = 0;
        if (atomic_compare_exchange_strong(&gaussian5_captured,
                                           &expected, 1)) {
            memcpy(gaussian5_bits, output, sizeof(gaussian5_bits));
        }
    }
    return result;
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

static void update_range(_Atomic int *minimum, _Atomic int *maximum, int value) {
    int current = atomic_load_explicit(minimum, memory_order_relaxed);
    while ((current == 0 || value < current) &&
           !atomic_compare_exchange_weak_explicit(minimum, &current, value,
                                                  memory_order_relaxed,
                                                  memory_order_relaxed)) {}
    current = atomic_load_explicit(maximum, memory_order_relaxed);
    while (value > current &&
           !atomic_compare_exchange_weak_explicit(maximum, &current, value,
                                                  memory_order_relaxed,
                                                  memory_order_relaxed)) {}
}

__attribute__((noinline))
static void *range_hook(void *output, float a, float b, float c, float d, float e) {
    void *result = ((range_fn)range_trampoline)(output, a, b, c, d, e);
    uint64_t call_index = atomic_fetch_add(&range_calls, 1);
    if (call_index == 0) {
        range_input[0] = fbits(a); range_input[1] = fbits(b);
        range_input[2] = fbits(c); range_input[3] = fbits(d);
        range_input[4] = fbits(e);
        range_output[0] = fbits(((float *)output)[0]);
        range_output[1] = fbits(((float *)output)[1]);
    }
    unsigned sample_index = atomic_fetch_add(&range_sample_count, 1);
    if (sample_index < RANGE_SAMPLE_LIMIT) {
        struct range_sample *sample = &range_samples[sample_index];
        sample->input[0] = fbits(a); sample->input[1] = fbits(b);
        sample->input[2] = fbits(c); sample->input[3] = fbits(d);
        sample->input[4] = fbits(e);
        sample->output[0] = fbits(((float *)output)[0]);
        sample->output[1] = fbits(((float *)output)[1]);
    }
    return result;
}

__attribute__((noinline))
static int radius_hook(const float *depth_range, int depth_type,
                       float a, float b, float c, float d) {
    int result = ((radius_fn)radius_trampoline)(depth_range, depth_type, a, b, c, d);
    if (atomic_fetch_add(&radius_calls, 1) == 0) {
        radius_depth_range[0] = fbits(depth_range[0]);
        radius_depth_range[1] = fbits(depth_range[1]);
        radius_depth_type = depth_type;
        radius_input[0] = fbits(a); radius_input[1] = fbits(b);
        radius_input[2] = fbits(c); radius_input[3] = fbits(d);
        radius_first_result = result;
    }
    if (result >= 0 && result <= RADIUS_RESULT_LIMIT) {
        unsigned char expected = 0;
        if (atomic_compare_exchange_strong(&radius_result_seen[result],
                                           &expected, 1)) {
            struct radius_sample *sample = &radius_result_samples[result];
            sample->depth_range[0] = fbits(depth_range[0]);
            sample->depth_range[1] = fbits(depth_range[1]);
            sample->depth_type = depth_type;
            sample->input[0] = fbits(a); sample->input[1] = fbits(b);
            sample->input[2] = fbits(c); sample->input[3] = fbits(d);
            sample->result = result;
        }
    }
    update_range(&radius_min, &radius_max, result);
    return result;
}

__attribute__((noinline))
static void *tiled_hook(void *output, void *dual, int radius,
                        float a, float b, float c, float d,
                        unsigned char flag, int device) {
    if (atomic_fetch_add(&tiled_calls, 1) == 0) {
        tiled_first_radius = radius;
        tiled_input[0] = fbits(a); tiled_input[1] = fbits(b);
        tiled_input[2] = fbits(c); tiled_input[3] = fbits(d);
        tiled_first_flag = flag;
        tiled_first_device = device;
    }
    return ((tiled_fn)tiled_trampoline)(output, dual, radius, a, b, c, d,
                                        flag, device);
}

__attribute__((noinline))
static void circle_vec_hook(void *output, const void *input, int radius) {
    atomic_fetch_add(&circle_vec_calls, 1);
    update_range(&circle_vec_min, &circle_vec_max, radius);
    ((circle_fn)circle_vec_trampoline)(output, input, radius);
}

__attribute__((noinline))
static void circle_float_hook(void *output, const void *input, int radius) {
    atomic_fetch_add(&circle_float_calls, 1);
    update_range(&circle_float_min, &circle_float_max, radius);
    ((circle_fn)circle_float_trampoline)(output, input, radius);
}

static int same_layer_table(const struct layer_table_sample *sample,
                            const uint8_t *context, uintptr_t begin,
                            size_t count) {
    uint32_t range_bits[2];
    int depth_type;
    memcpy(range_bits, context + 0x60, sizeof(range_bits));
    memcpy(&depth_type, context + 0x68, sizeof(depth_type));
    if (sample->range_bits[0] != range_bits[0] ||
        sample->range_bits[1] != range_bits[1] ||
        sample->depth_type != depth_type ||
        sample->b0 != *(const int *)(context + 0xb0) ||
        sample->b4 != context[0xb4] || sample->b5 != context[0xb5] ||
        sample->record_count != count)
        return 0;
    for (size_t i = 0; i < count && i < LAYER_TABLE_RECORD_LIMIT; ++i) {
        const uint8_t *record = (const uint8_t *)(begin + i * 0x40);
        uint32_t lower_bits, upper_bits;
        int radius;
        memcpy(&lower_bits, record + 0x00, 4);
        memcpy(&upper_bits, record + 0x04, 4);
        memcpy(&radius, record + 0x08, 4);
        if (sample->records[i].lower_bits != lower_bits ||
            sample->records[i].upper_bits != upper_bits ||
            sample->records[i].radius != radius)
            return 0;
    }
    return 1;
}

static void capture_layer_table(const uint8_t *context, uintptr_t begin,
                                size_t count) {
    while (atomic_flag_test_and_set_explicit(&layer_table_lock,
                                              memory_order_acquire)) {}
    for (unsigned i = 0; i < layer_table_sample_count; ++i) {
        if (same_layer_table(&layer_table_samples[i], context, begin, count)) {
            atomic_flag_clear_explicit(&layer_table_lock, memory_order_release);
            return;
        }
    }
    if (layer_table_sample_count < LAYER_TABLE_LIMIT) {
        struct layer_table_sample *sample =
            &layer_table_samples[layer_table_sample_count++];
        memcpy(sample->range_bits, context + 0x60,
               sizeof(sample->range_bits));
        memcpy(&sample->depth_type, context + 0x68,
               sizeof(sample->depth_type));
        memcpy(&sample->b0, context + 0xb0, sizeof(sample->b0));
        sample->b4 = context[0xb4];
        sample->b5 = context[0xb5];
        memcpy(&sample->primary_width, context + 0x10, 4);
        memcpy(&sample->primary_height, context + 0x14, 4);
        memcpy(&sample->secondary_width, context + 0x40, 4);
        memcpy(&sample->secondary_height, context + 0x44, 4);
        sample->secondary_present = *(const uintptr_t *)(context + 0x50) != 0;
        sample->record_count = (unsigned)count;
        size_t stored = count;
        if (stored > LAYER_TABLE_RECORD_LIMIT)
            stored = LAYER_TABLE_RECORD_LIMIT;
        for (size_t i = 0; i < stored; ++i) {
            const uint8_t *record = (const uint8_t *)(begin + i * 0x40);
            struct layer_record_sample *item = &sample->records[i];
            memcpy(&item->lower_bits, record + 0x00, 4);
            memcpy(&item->upper_bits, record + 0x04, 4);
            memcpy(&item->radius, record + 0x08, 4);
            uintptr_t primary_begin, primary_end;
            uintptr_t secondary_begin, secondary_end;
            memcpy(&primary_begin, record + 0x10, 8);
            memcpy(&primary_end, record + 0x18, 8);
            memcpy(&secondary_begin, record + 0x28, 8);
            memcpy(&secondary_end, record + 0x30, 8);
            item->primary_count = primary_end >= primary_begin
                ? (primary_end - primary_begin) / 8 : UINT64_MAX;
            item->secondary_count = secondary_end >= secondary_begin
                ? (secondary_end - secondary_begin) / 8 : UINT64_MAX;
        }
    }
    atomic_flag_clear_explicit(&layer_table_lock, memory_order_release);
}

__attribute__((noinline))
static void layer_transition_hook(void *context, void *destination,
                                  const void *source_record,
                                  const void *boundary_record) {
    ((layer_transition_fn)layer_transition_trampoline)(
        context, destination, source_record, boundary_record);
    atomic_fetch_add(&layer_transition_calls, 1);

    float source_upper, boundary_upper;
    memcpy(&source_upper, (const uint8_t *)source_record + 0x04, 4);
    memcpy(&boundary_upper, (const uint8_t *)boundary_record + 0x04, 4);
    if (source_upper < boundary_upper)
        atomic_fetch_add(&layer_transition_less_calls, 1);
    else if (source_upper > boundary_upper)
        atomic_fetch_add(&layer_transition_greater_calls, 1);
    else
        atomic_fetch_add(&layer_transition_equal_calls, 1);

    uintptr_t coords_begin, coords_end;
    memcpy(&coords_begin, (const uint8_t *)source_record + 0x10, 8);
    memcpy(&coords_end, (const uint8_t *)source_record + 0x18, 8);
    if (coords_begin == 0 || coords_end <= coords_begin)
        return;
    unsigned index = atomic_fetch_add(&layer_transition_sample_count, 1);
    if (index >= LAYER_TRANSITION_SAMPLE_LIMIT)
        return;

    struct layer_transition_sample *sample = &layer_transition_samples[index];
    memcpy(&sample->source_upper_bits,
           (const uint8_t *)source_record + 0x04, 4);
    memcpy(&sample->boundary_upper_bits,
           (const uint8_t *)boundary_record + 0x04, 4);
    memcpy(&sample->source_radius,
           (const uint8_t *)source_record + 0x08, 4);
    memcpy(&sample->boundary_radius,
           (const uint8_t *)boundary_record + 0x08, 4);
    memcpy(&sample->b0, (const uint8_t *)context + 0xb0, 4);
    sample->b4 = ((const uint8_t *)context)[0xb4];
    sample->b5 = ((const uint8_t *)context)[0xb5];
    memcpy(&sample->x, (const void *)coords_begin, 4);
    memcpy(&sample->y, (const void *)(coords_begin + 4), 4);

    uintptr_t image;
    memcpy(&image, (const uint8_t *)context + 0x70, 8);
    int color_stride, depth_stride, destination_stride;
    uintptr_t color_data, depth_data, destination_data;
    memcpy(&color_stride, (const void *)(image + 0x18), 4);
    memcpy(&color_data, (const void *)(image + 0x20), 8);
    memcpy(&depth_stride, (const uint8_t *)context + 0x18, 4);
    memcpy(&depth_data, (const uint8_t *)context + 0x20, 8);
    memcpy(&destination_stride, (const uint8_t *)destination + 0x18, 4);
    memcpy(&destination_data, (const uint8_t *)destination + 0x20, 8);
    size_t color_index = (size_t)(sample->y * color_stride + sample->x) * 16;
    size_t depth_index = (size_t)(sample->y * depth_stride + sample->x) * 4;
    size_t destination_index =
        (size_t)(sample->y * destination_stride + sample->x) * 16;
    memcpy(sample->color_bits, (const void *)(color_data + color_index), 12);
    memcpy(&sample->depth_bits, (const void *)(depth_data + depth_index), 4);
    memcpy(sample->output_bits,
           (const void *)(destination_data + destination_index), 16);
}

__attribute__((noinline))
static void *layer_records_hook(void *output, void *context) {
    void *result = ((layer_records_fn)layer_records_trampoline)(output, context);
    atomic_fetch_add(&layer_records_calls, 1);

    uintptr_t begin = ((uintptr_t *)output)[0];
    uintptr_t end = ((uintptr_t *)output)[1];
    if (begin != 0 && end >= begin && (end - begin) % 0x40 == 0) {
        size_t count = (end - begin) / 0x40;
        for (size_t i = 0; i < count; ++i) {
            const uint8_t *record = (const uint8_t *)(begin + i * 0x40);
            int radius;
            memcpy(&radius, record + 0x08, sizeof(radius));
            if (radius >= 0 && radius <= LAYER_RADIUS_LIMIT)
                atomic_fetch_add(&layer_radius_incidence[radius], 1);
        }
        capture_layer_table((const uint8_t *)context, begin, count);

        int expected = 0;
        if (atomic_compare_exchange_strong(&layer_capture_state, &expected, 1)) {
            memcpy(layer_context_a0_bits, (const uint8_t *)context + 0xa0,
                   sizeof(layer_context_a0_bits));
            memcpy(layer_context_range_bits, (const uint8_t *)context + 0x60,
                   sizeof(layer_context_range_bits));
            memcpy(&layer_context_depth_type,
                   (const uint8_t *)context + 0x68,
                   sizeof(layer_context_depth_type));
            memcpy(&layer_context_b0, (const uint8_t *)context + 0xb0,
                   sizeof(layer_context_b0));
            memcpy(&layer_context_b4, (const uint8_t *)context + 0xb4,
                   sizeof(layer_context_b4));
            memcpy(&layer_context_b5, (const uint8_t *)context + 0xb5,
                   sizeof(layer_context_b5));
            if (count > LAYER_RECORD_LIMIT) count = LAYER_RECORD_LIMIT;
            layer_record_sample_count = (unsigned)count;
            for (size_t i = 0; i < count; ++i) {
                const uint8_t *record = (const uint8_t *)(begin + i * 0x40);
                struct layer_record_sample *sample = &layer_record_samples[i];
                memcpy(&sample->lower_bits, record + 0x00, 4);
                memcpy(&sample->upper_bits, record + 0x04, 4);
                memcpy(&sample->radius, record + 0x08, 4);
                uintptr_t primary_begin, primary_end;
                uintptr_t secondary_begin, secondary_end;
                memcpy(&primary_begin, record + 0x10, 8);
                memcpy(&primary_end, record + 0x18, 8);
                memcpy(&secondary_begin, record + 0x28, 8);
                memcpy(&secondary_end, record + 0x30, 8);
                sample->primary_count = primary_end >= primary_begin
                    ? (primary_end - primary_begin) / 8 : UINT64_MAX;
                sample->secondary_count = secondary_end >= secondary_begin
                    ? (secondary_end - secondary_begin) / 8 : UINT64_MAX;
            }
            atomic_store(&layer_capture_state, 2);
        }
    }
    return result;
}

__attribute__((noinline))
static void resample_hook(void *output, void *input,
                          const double *offset, const double *scale) {
    if (layer_filter_depth != 0) {
        atomic_fetch_add(&layer_filter_resample_calls, 1);
        unsigned index = atomic_fetch_add(&layer_resample_sample_count, 1);
        if (index < LAYER_RESAMPLE_SAMPLE_LIMIT) {
            struct layer_resample_sample *sample =
                &layer_resample_samples[index];
            memcpy(&sample->output_width, (const uint8_t *)output + 0x10, 4);
            memcpy(&sample->output_height, (const uint8_t *)output + 0x14, 4);
            memcpy(&sample->input_width, (const uint8_t *)input + 0x10, 4);
            memcpy(&sample->input_height, (const uint8_t *)input + 0x14, 4);
            sample->offset_bits[0] = dbits(offset[0]);
            sample->offset_bits[1] = dbits(offset[1]);
            sample->scale_bits[0] = dbits(scale[0]);
            sample->scale_bits[1] = dbits(scale[1]);
            sample->diameter = layer_filter_diameter;
            sample->depth_type = layer_filter_depth_type;
            memcpy(sample->first_rect, layer_filter_first_rect,
                   sizeof(sample->first_rect));
        }
    }
    ((resample_fn)resample_trampoline)(output, input, offset, scale);
}

__attribute__((noinline))
static void layer_filter_hook(void *output, void *input,
                              const int *first_rect, const int *second_rect,
                              int diameter, int depth_type) {
    atomic_fetch_add(&layer_filter_calls, 1);
    if (memcmp(first_rect, second_rect, sizeof(int) * 4) == 0)
        atomic_fetch_add(&layer_filter_equal_rect_calls, 1);
    else
        atomic_fetch_add(&layer_filter_distinct_rect_calls, 1);
    int max_diameter = depth_type == 0 ? 13 : 65;
    int branch;
    if (diameter <= 2) {
        branch = 0;
        atomic_fetch_add(&layer_filter_copy_calls, 1);
    } else if (max_diameter > diameter) {
        branch = 1;
        atomic_fetch_add(&layer_filter_small_calls, 1);
    } else {
        branch = 2;
        atomic_fetch_add(&layer_filter_large_calls, 1);
    }
    unsigned index = atomic_fetch_add(&layer_filter_sample_count, 1);
    if (index < LAYER_FILTER_SAMPLE_LIMIT) {
        struct layer_filter_sample *sample = &layer_filter_samples[index];
        memcpy(&sample->input_width, (const uint8_t *)input + 0x10, 4);
        memcpy(&sample->input_height, (const uint8_t *)input + 0x14, 4);
        sample->diameter = diameter;
        sample->depth_type = depth_type;
        memcpy(sample->first_rect, first_rect, sizeof(sample->first_rect));
        memcpy(sample->second_rect, second_rect, sizeof(sample->second_rect));
        sample->branch = branch;
    }
    layer_filter_diameter = diameter;
    layer_filter_depth_type = depth_type;
    memcpy(layer_filter_first_rect, first_rect,
           sizeof(layer_filter_first_rect));
    ++layer_filter_depth;
    ((layer_filter_fn)layer_filter_trampoline)(
        output, input, first_rect, second_rect, diameter, depth_type);
    --layer_filter_depth;
}

__attribute__((constructor))
static void install_hooks(void) {
    libcp_base = find_libcp_base();
    if (libcp_base == 0) return;
    range_trampoline = install_hook(0x2c5710, 15, (const void *)&range_hook);
    radius_trampoline = install_hook(0x2c5590, 14, (const void *)&radius_hook);
    tiled_trampoline = install_hook(0x2a4cf0, 18, (const void *)&tiled_hook);
    circle_vec_trampoline = install_hook(0x0d05b0, 20, (const void *)&circle_vec_hook);
    circle_float_trampoline = install_hook(0x0d09b0, 20, (const void *)&circle_float_hook);
    layer_records_trampoline = install_hook(0x2a40b0, 15,
                                            (const void *)&layer_records_hook);
    layer_transition_trampoline = install_hook(
        0x2a47f0, 13, (const void *)&layer_transition_hook);
    layer_filter_trampoline = install_hook(
        0x2b2450, 13, (const void *)&layer_filter_hook);
    resample_trampoline = install_hook(
        0x2b2be0, 13, (const void *)&resample_hook);
    gaussian_trampoline = install_hook(
        0x096980, 13, (const void *)&gaussian_hook);
}

__attribute__((destructor))
static void write_report(void) {
    const char *path = getenv("L16_DOF_MATH_OUT");
    if (path == NULL) return;
    FILE *output = fopen(path, "w");
    if (output == NULL) return;
    fprintf(output,
            "{\n"
            "  \"range_calls\": %llu,\n"
            "  \"range_input_bits\": [\"%08x\",\"%08x\",\"%08x\",\"%08x\",\"%08x\"],\n"
            "  \"range_output_bits\": [\"%08x\",\"%08x\"],\n"
            "  \"radius_calls\": %llu,\n"
            "  \"radius_depth_range_bits\": [\"%08x\",\"%08x\"],\n"
            "  \"radius_depth_type\": %d,\n"
            "  \"radius_input_bits\": [\"%08x\",\"%08x\",\"%08x\",\"%08x\"],\n"
            "  \"radius_first_result\": %d,\n"
            "  \"radius_min\": %d,\n"
            "  \"radius_max\": %d,\n"
            "  \"tiled_calls\": %llu,\n"
            "  \"tiled_first_radius\": %d,\n"
            "  \"tiled_input_bits\": [\"%08x\",\"%08x\",\"%08x\",\"%08x\"],\n"
            "  \"tiled_first_flag\": %d,\n"
            "  \"tiled_first_device\": %d,\n"
            "  \"circle_vec_calls\": %llu,\n"
            "  \"circle_vec_radius_min\": %d,\n"
            "  \"circle_vec_radius_max\": %d,\n"
            "  \"circle_float_calls\": %llu,\n"
            "  \"circle_float_radius_min\": %d,\n"
            "  \"circle_float_radius_max\": %d,\n"
            "  \"layer_records_calls\": %llu,\n"
            "  \"layer_context_a0_bits\": [\"%08x\",\"%08x\",\"%08x\",\"%08x\"],\n"
            "  \"layer_context_range_bits\": [\"%08x\",\"%08x\"],\n"
            "  \"layer_context_depth_type\": %d,\n"
            "  \"layer_context_b0\": %d,\n"
            "  \"layer_context_b4\": %u,\n"
            "  \"layer_context_b5\": %u",
            (unsigned long long)atomic_load(&range_calls),
            range_input[0], range_input[1], range_input[2], range_input[3], range_input[4],
            range_output[0], range_output[1],
            (unsigned long long)atomic_load(&radius_calls),
            radius_depth_range[0], radius_depth_range[1], radius_depth_type,
            radius_input[0], radius_input[1], radius_input[2], radius_input[3],
            radius_first_result, atomic_load(&radius_min), atomic_load(&radius_max),
            (unsigned long long)atomic_load(&tiled_calls), tiled_first_radius,
            tiled_input[0], tiled_input[1], tiled_input[2], tiled_input[3],
            tiled_first_flag, tiled_first_device,
            (unsigned long long)atomic_load(&circle_vec_calls),
            atomic_load(&circle_vec_min), atomic_load(&circle_vec_max),
            (unsigned long long)atomic_load(&circle_float_calls),
            atomic_load(&circle_float_min), atomic_load(&circle_float_max),
            (unsigned long long)atomic_load(&layer_records_calls),
            layer_context_a0_bits[0], layer_context_a0_bits[1],
            layer_context_a0_bits[2], layer_context_a0_bits[3],
            layer_context_range_bits[0], layer_context_range_bits[1],
            layer_context_depth_type, layer_context_b0,
            (unsigned)layer_context_b4, (unsigned)layer_context_b5);
    unsigned stored_ranges = atomic_load(&range_sample_count);
    if (stored_ranges > RANGE_SAMPLE_LIMIT) stored_ranges = RANGE_SAMPLE_LIMIT;
    fprintf(output, ",\n  \"range_samples\": [");
    for (unsigned i = 0; i < stored_ranges; ++i) {
        const struct range_sample *sample = &range_samples[i];
        fprintf(output,
                "%s{\"input_bits\":[\"%08x\",\"%08x\",\"%08x\",\"%08x\",\"%08x\"],"
                "\"output_bits\":[\"%08x\",\"%08x\"]}",
                i == 0 ? "" : ",",
                sample->input[0], sample->input[1], sample->input[2],
                sample->input[3], sample->input[4], sample->output[0],
                sample->output[1]);
    }
    fprintf(output, "],\n  \"radius_result_samples\": [");
    int first = 1;
    for (int result = 0; result <= RADIUS_RESULT_LIMIT; ++result) {
        if (!atomic_load(&radius_result_seen[result])) continue;
        const struct radius_sample *sample = &radius_result_samples[result];
        fprintf(output,
                "%s{\"depth_range_bits\":[\"%08x\",\"%08x\"],"
                "\"depth_type\":%d,"
                "\"input_bits\":[\"%08x\",\"%08x\",\"%08x\",\"%08x\"],"
                "\"result\":%d}",
                first ? "" : ",", sample->depth_range[0],
                sample->depth_range[1], sample->depth_type, sample->input[0],
                sample->input[1], sample->input[2], sample->input[3],
                sample->result);
        first = 0;
    }
    fprintf(output, "],\n  \"layer_record_sample_count\": %u,\n",
            layer_record_sample_count);
    fprintf(output, "  \"layer_record_samples\": [");
    for (unsigned i = 0; i < layer_record_sample_count; ++i) {
        const struct layer_record_sample *sample = &layer_record_samples[i];
        fprintf(output,
                "%s{\"lower_bits\":\"%08x\",\"upper_bits\":\"%08x\"," 
                "\"radius\":%d,\"primary_count\":%llu,"
                "\"secondary_count\":%llu}",
                i == 0 ? "" : ",", sample->lower_bits, sample->upper_bits,
                sample->radius, (unsigned long long)sample->primary_count,
                (unsigned long long)sample->secondary_count);
    }
    fprintf(output, "],\n  \"layer_radius_incidence\": [");
    int first_radius = 1;
    for (int radius = 0; radius <= LAYER_RADIUS_LIMIT; ++radius) {
        uint64_t count = atomic_load(&layer_radius_incidence[radius]);
        if (count == 0) continue;
        fprintf(output, "%s{\"radius\":%d,\"count\":%llu}",
                first_radius ? "" : ",", radius,
                (unsigned long long)count);
        first_radius = 0;
    }
    fprintf(output, "],\n  \"layer_table_samples\": [");
    for (unsigned i = 0; i < layer_table_sample_count; ++i) {
        const struct layer_table_sample *sample = &layer_table_samples[i];
        fprintf(output,
                "%s{\"range_bits\":[\"%08x\",\"%08x\"],"
                "\"depth_type\":%d,\"b0\":%d,\"b4\":%u,\"b5\":%u,"
                "\"primary_dims\":[%d,%d],\"secondary_dims\":[%d,%d],"
                "\"secondary_present\":%u,\"record_count\":%u,\"records\":[",
                i == 0 ? "" : ",", sample->range_bits[0],
                sample->range_bits[1], sample->depth_type, sample->b0,
                (unsigned)sample->b4, (unsigned)sample->b5,
                sample->primary_width, sample->primary_height,
                sample->secondary_width, sample->secondary_height,
                (unsigned)sample->secondary_present, sample->record_count);
        unsigned stored = sample->record_count;
        if (stored > LAYER_TABLE_RECORD_LIMIT)
            stored = LAYER_TABLE_RECORD_LIMIT;
        for (unsigned j = 0; j < stored; ++j) {
            const struct layer_record_sample *item = &sample->records[j];
            fprintf(output,
                    "%s{\"lower_bits\":\"%08x\",\"upper_bits\":\"%08x\","
                    "\"radius\":%d,\"primary_count\":%llu,"
                    "\"secondary_count\":%llu}",
                    j == 0 ? "" : ",", item->lower_bits,
                    item->upper_bits, item->radius,
                    (unsigned long long)item->primary_count,
                    (unsigned long long)item->secondary_count);
        }
        fprintf(output, "]}");
    }
    fprintf(output,
            "],\n  \"layer_transition_calls\": %llu,\n"
            "  \"layer_transition_relation_calls\": {"
            "\"less\":%llu,\"equal\":%llu,\"greater\":%llu},\n"
            "  \"layer_transition_samples\": [",
            (unsigned long long)atomic_load(&layer_transition_calls),
            (unsigned long long)atomic_load(&layer_transition_less_calls),
            (unsigned long long)atomic_load(&layer_transition_equal_calls),
            (unsigned long long)atomic_load(&layer_transition_greater_calls));
    unsigned transition_count = atomic_load(&layer_transition_sample_count);
    if (transition_count > LAYER_TRANSITION_SAMPLE_LIMIT)
        transition_count = LAYER_TRANSITION_SAMPLE_LIMIT;
    for (unsigned i = 0; i < transition_count; ++i) {
        const struct layer_transition_sample *sample =
            &layer_transition_samples[i];
        fprintf(output,
                "%s{\"source_upper_bits\":\"%08x\","
                "\"boundary_upper_bits\":\"%08x\","
                "\"source_radius\":%d,\"boundary_radius\":%d,"
                "\"b0\":%d,\"b4\":%u,\"b5\":%u,"
                "\"xy\":[%d,%d],"
                "\"color_bits\":[\"%08x\",\"%08x\",\"%08x\"],"
                "\"depth_bits\":\"%08x\","
                "\"output_bits\":[\"%08x\",\"%08x\",\"%08x\",\"%08x\"]}",
                i == 0 ? "" : ",", sample->source_upper_bits,
                sample->boundary_upper_bits, sample->source_radius,
                sample->boundary_radius, sample->b0,
                (unsigned)sample->b4, (unsigned)sample->b5,
                sample->x, sample->y, sample->color_bits[0],
                sample->color_bits[1], sample->color_bits[2],
                sample->depth_bits, sample->output_bits[0],
                sample->output_bits[1], sample->output_bits[2],
                sample->output_bits[3]);
    }
    fprintf(output,
            "],\n  \"gaussian5_captured\": %u,\n"
            "  \"gaussian5_bits\": [\"%08x\",\"%08x\",\"%08x\","
            "\"%08x\",\"%08x\"],\n"
            "  \"layer_filter_calls\": %llu,\n"
            "  \"layer_filter_branch_calls\": {"
            "\"copy\":%llu,\"small\":%llu,\"large\":%llu},\n"
            "  \"layer_filter_rect_calls\": {"
            "\"equal\":%llu,\"distinct\":%llu},\n"
            "  \"layer_filter_samples\": [",
            atomic_load(&gaussian5_captured),
            gaussian5_bits[0], gaussian5_bits[1], gaussian5_bits[2],
            gaussian5_bits[3], gaussian5_bits[4],
            (unsigned long long)atomic_load(&layer_filter_calls),
            (unsigned long long)atomic_load(&layer_filter_copy_calls),
            (unsigned long long)atomic_load(&layer_filter_small_calls),
            (unsigned long long)atomic_load(&layer_filter_large_calls),
            (unsigned long long)atomic_load(&layer_filter_equal_rect_calls),
            (unsigned long long)atomic_load(&layer_filter_distinct_rect_calls));
    unsigned filter_count = atomic_load(&layer_filter_sample_count);
    if (filter_count > LAYER_FILTER_SAMPLE_LIMIT)
        filter_count = LAYER_FILTER_SAMPLE_LIMIT;
    for (unsigned i = 0; i < filter_count; ++i) {
        const struct layer_filter_sample *sample = &layer_filter_samples[i];
        fprintf(output,
                "%s{\"input_dims\":[%d,%d],\"diameter\":%d,"
                "\"depth_type\":%d,\"first_rect\":[%d,%d,%d,%d],"
                "\"second_rect\":[%d,%d,%d,%d],\"branch\":%d}",
                i == 0 ? "" : ",", sample->input_width,
                sample->input_height, sample->diameter, sample->depth_type,
                sample->first_rect[0], sample->first_rect[1],
                sample->first_rect[2], sample->first_rect[3],
                sample->second_rect[0], sample->second_rect[1],
                sample->second_rect[2], sample->second_rect[3],
                sample->branch);
    }
    fprintf(output,
            "],\n  \"layer_filter_resample_calls\": %llu,\n"
            "  \"layer_resample_samples\": [",
            (unsigned long long)atomic_load(&layer_filter_resample_calls));
    unsigned resample_count = atomic_load(&layer_resample_sample_count);
    if (resample_count > LAYER_RESAMPLE_SAMPLE_LIMIT)
        resample_count = LAYER_RESAMPLE_SAMPLE_LIMIT;
    for (unsigned i = 0; i < resample_count; ++i) {
        const struct layer_resample_sample *sample =
            &layer_resample_samples[i];
        fprintf(output,
                "%s{\"output_dims\":[%d,%d],\"input_dims\":[%d,%d],"
                "\"diameter\":%d,\"depth_type\":%d,"
                "\"first_rect\":[%d,%d,%d,%d],"
                "\"offset_bits\":[\"%016llx\",\"%016llx\"],"
                "\"scale_bits\":[\"%016llx\",\"%016llx\"]}",
                i == 0 ? "" : ",", sample->output_width,
                sample->output_height, sample->input_width,
                sample->input_height, sample->diameter, sample->depth_type,
                sample->first_rect[0], sample->first_rect[1],
                sample->first_rect[2], sample->first_rect[3],
                (unsigned long long)sample->offset_bits[0],
                (unsigned long long)sample->offset_bits[1],
                (unsigned long long)sample->scale_bits[0],
                (unsigned long long)sample->scale_bits[1]);
    }
    fprintf(output, "]\n}\n");
    fclose(output);
}
