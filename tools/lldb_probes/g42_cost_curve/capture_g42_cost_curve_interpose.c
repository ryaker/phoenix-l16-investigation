#include <mach-o/dyld.h>
#include <stdatomic.h>
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
    int32_t allocation_height;
    void *data;
    void *allocation;
} Image;

typedef void (*cost_fn)(uint8_t *, int32_t, int32_t, uint16_t *);

static uintptr_t libcp_base;
static void *cost_trampoline;
static atomic_int capture_state;
static int32_t target_x = 1040;
static int32_t target_y = 780;

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

static void *pointer_at(const void *base, size_t offset) {
    void *value = NULL;
    memcpy(&value, (const uint8_t *)base + offset, sizeof(value));
    return value;
}

static uint32_t word_at(const void *base, size_t offset) {
    uint32_t value;
    memcpy(&value, (const uint8_t *)base + offset, sizeof(value));
    return value;
}

static int valid_image(const Image *image) {
    return image != NULL && image->data != NULL && image->width > 0 &&
           image->height > 0 && image->stride >= image->width;
}

static int write_bytes(const char *path, const void *data, size_t size) {
    FILE *output = fopen(path, "wb");
    if (output == NULL) return 0;
    int ok = fwrite(data, 1, size, output) == size;
    ok &= fclose(output) == 0;
    return ok;
}

static int write_image(const char *path, const Image *image) {
    FILE *output = fopen(path, "wb");
    if (output == NULL) return 0;
    size_t row_size = (size_t)image->width * 4;
    for (int32_t y = 0; y < image->height; ++y) {
        const uint8_t *row = (const uint8_t *)image->data +
                             (size_t)y * (size_t)image->stride * 4;
        if (fwrite(row, 1, row_size, output) != row_size) {
            fclose(output);
            return 0;
        }
    }
    return fclose(output) == 0;
}

static void print_hex(FILE *output, const uint8_t *data, size_t size) {
    for (size_t i = 0; i < size; ++i) fprintf(output, "%02x", data[i]);
}

static size_t vector_bytes(void *object, size_t item_size, void **begin_out) {
    if (object == NULL) return 0;
    void *begin = pointer_at(object, 0);
    void *end = pointer_at(object, 8);
    if (begin == NULL || end == NULL || (uintptr_t)end < (uintptr_t)begin)
        return 0;
    size_t bytes = (uintptr_t)end - (uintptr_t)begin;
    if (item_size == 0 || bytes % item_size != 0) return 0;
    *begin_out = begin;
    return bytes;
}

static int preserve_packet(uint8_t *context, int32_t lower, int32_t count,
                           const uint16_t *curve) {
    const char *directory = getenv("L16_G42_CURVE_DIR");
    if (directory == NULL || count <= 0 || count > 4096) return 0;

    Image *anchor = pointer_at(context, 0);
    void *source_vector = pointer_at(context, 8);
    void *record_vector = pointer_at(context, 0x10);
    void *lookup_vector = pointer_at(context, 0x18);
    void *source_begin = NULL;
    void *record_begin = NULL;
    void *lookup_begin = NULL;
    size_t source_bytes = vector_bytes(source_vector, 16, &source_begin);
    size_t record_bytes = vector_bytes(record_vector, 0x50, &record_begin);
    size_t lookup_bytes = vector_bytes(lookup_vector, 4, &lookup_begin);
    size_t source_count = source_bytes / 16;
    size_t record_count = record_bytes / 0x50;
    size_t lookup_count = lookup_bytes / 4;
    if (!valid_image(anchor) || source_count != 4 || record_count != 4 ||
        lookup_count < (size_t)(lower + count))
        return 0;

    Image *images[5] = {anchor, NULL, NULL, NULL, NULL};
    for (size_t i = 0; i < source_count; ++i) {
        images[i + 1] = pointer_at((uint8_t *)source_begin + 16 * i, 0);
        if (!valid_image(images[i + 1])) return 0;
    }

    char path[1024];
    int ok = 1;
    snprintf(path, sizeof(path), "%s/local_curve.u16le", directory);
    ok &= write_bytes(path, curve, (size_t)count * 2);
    snprintf(path, sizeof(path), "%s/lookup.f32le", directory);
    ok &= write_bytes(path, lookup_begin, lookup_bytes);
    snprintf(path, sizeof(path), "%s/projection_records.bin", directory);
    ok &= write_bytes(path, record_begin, record_bytes);
    for (size_t i = 0; i < 5; ++i) {
        snprintf(path, sizeof(path), "%s/image%zu.rgba8", directory, i);
        ok &= write_image(path, images[i]);
    }

    snprintf(path, sizeof(path), "%s/report.json", directory);
    FILE *report = fopen(path, "w");
    if (report == NULL) return 0;
    fprintf(report,
            "{\n"
            "  \"reference_pixel\": [%d, %d],\n"
            "  \"lower_hypothesis\": %d,\n"
            "  \"hypothesis_count\": %d,\n"
            "  \"lookup_count\": %zu,\n"
            "  \"source_count\": %zu,\n"
            "  \"projection_record_count\": %zu,\n"
            "  \"cap_hex\": \"",
            target_x, target_y, lower, count, lookup_count, source_count,
            record_count);
    print_hex(report, context + 0x40, 16);
    fprintf(report, "\",\n  \"anchor_rows_hex\": [\"");
    print_hex(report, context + 0x50, 16);
    fprintf(report, "\", \"");
    print_hex(report, context + 0x60, 16);
    fprintf(report, "\", \"");
    print_hex(report, context + 0x70, 16);
    fprintf(report, "\"],\n  \"weights_hex\": \"");
    void *weights = pointer_at(context, 0x80);
    if (weights != NULL) print_hex(report, weights, source_count * 8);
    fprintf(report, "\",\n  \"images\": [\n");
    for (size_t i = 0; i < 5; ++i) {
        fprintf(report,
                "    {\"ordinal\": %zu, \"origin\": [%d,%d], "
                "\"bounds\": [%d,%d], \"size\": [%d,%d], "
                "\"stride\": %d, \"file\": \"image%zu.rgba8\"}%s\n",
                i, images[i]->origin_x, images[i]->origin_y,
                images[i]->limit_x, images[i]->limit_y,
                images[i]->width, images[i]->height, images[i]->stride, i,
                i == 4 ? "" : ",");
    }
    fprintf(report,
            "  ],\n"
            "  \"files\": {\"curve\": \"local_curve.u16le\", "
            "\"lookup\": \"lookup.f32le\", "
            "\"projection_records\": \"projection_records.bin\"},\n"
            "  \"capture_ok\": %s\n"
            "}\n",
            ok ? "true" : "false");
    ok &= fclose(report) == 0;
    return ok;
}

__attribute__((noinline))
static void cost_hook(uint8_t *context, int32_t lower, int32_t count,
                      uint16_t *curve) {
    float u;
    float v;
    uint32_t u_bits = word_at(context, 0x20);
    uint32_t v_bits = word_at(context, 0x24);
    memcpy(&u, &u_bits, sizeof(u));
    memcpy(&v, &v_bits, sizeof(v));
    int wanted = u == (float)target_x && v == (float)target_y;
    int expected = 0;
    int capture = wanted && atomic_compare_exchange_strong(
                                &capture_state, &expected, 1);
    ((cost_fn)cost_trampoline)(context, lower, count, curve);
    if (capture) {
        int ok = preserve_packet(context, lower, count, curve);
        atomic_store(&capture_state, ok ? 2 : -1);
    }
}

__attribute__((constructor))
static void install_g42_curve_hook(void) {
    const char *x_text = getenv("L16_G42_TARGET_X");
    const char *y_text = getenv("L16_G42_TARGET_Y");
    if (x_text != NULL) target_x = (int32_t)strtol(x_text, NULL, 10);
    if (y_text != NULL) target_y = (int32_t)strtol(y_text, NULL, 10);
    libcp_base = find_libcp_base();
    if (libcp_base == 0) return;
    cost_trampoline = install_hook(0x2732f0, 13, (const void *)&cost_hook);
}

__attribute__((destructor))
static void write_capture_status(void) {
    const char *directory = getenv("L16_G42_CURVE_DIR");
    if (directory == NULL) return;
    char path[1024];
    snprintf(path, sizeof(path), "%s/status.txt", directory);
    FILE *output = fopen(path, "w");
    if (output == NULL) return;
    fprintf(output, "%d\n", atomic_load(&capture_state));
    fclose(output);
}
