#include <mach-o/dyld.h>
#include <dlfcn.h>
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

typedef void (*producer_fn)(Image *, const void *);

static uintptr_t libcp_base;
static void *producer_trampoline;
static atomic_int capture_state;

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

static int valid_source(const Image *image) {
    return image != NULL && image->data != NULL && image->origin_x == 0 &&
           image->origin_y == 0 && image->width == 2080 &&
           image->height == 1560 && image->stride >= image->width;
}

static int write_source(const Image *image, uint32_t stereo_index) {
    const char *directory = getenv("L16_INDEX5_CAPTURE_DIR");
    if (directory == NULL) return 0;

    char path[1024];
    snprintf(path, sizeof(path), "%s/index5_hypothesis_index.u16le", directory);
    FILE *output = fopen(path, "wb");
    if (output == NULL) return 0;
    size_t row_size = (size_t)image->width * sizeof(uint16_t);
    int ok = 1;
    for (int32_t y = 0; y < image->height; ++y) {
        const uint8_t *row = (const uint8_t *)image->data +
                             (size_t)y * (size_t)image->stride * sizeof(uint16_t);
        if (fwrite(row, 1, row_size, output) != row_size) {
            ok = 0;
            break;
        }
    }
    ok &= fclose(output) == 0;

    snprintf(path, sizeof(path), "%s/report.json", directory);
    FILE *report = fopen(path, "w");
    if (report == NULL) return 0;
    fprintf(report,
            "{\n"
            "  \"hook_va\": \"0x299c70\",\n"
            "  \"stereo_index\": %u,\n"
            "  \"origin\": [%d, %d],\n"
            "  \"size\": [%d, %d],\n"
            "  \"stride\": %d,\n"
            "  \"logical_bytes\": %zu,\n"
            "  \"capture_ok\": %s\n"
            "}\n",
            stereo_index, image->origin_x, image->origin_y, image->width,
            image->height, image->stride,
            (size_t)image->width * (size_t)image->height * sizeof(uint16_t),
            ok ? "true" : "false");
    ok &= fclose(report) == 0;
    return ok;
}

__attribute__((noinline))
static void producer_hook(Image *destination, const void *source) {
    uintptr_t caller = (uintptr_t)__builtin_return_address(0);
    uintptr_t stereo_object;
    __asm__ volatile("movq %%r12, %0" : "=r"(stereo_object));
    uint32_t stereo_index = UINT32_MAX;
    if (caller == libcp_base + 0x26e4d5 && stereo_object != 0)
        memcpy(&stereo_index, (const void *)(stereo_object + 8), sizeof(stereo_index));

    ((producer_fn)producer_trampoline)(destination, source);
    if (stereo_index != 5 || !valid_source(destination)) return;

    int expected = 0;
    if (!atomic_compare_exchange_strong(&capture_state, &expected, 1)) return;
    int ok = write_source(destination, stereo_index);
    atomic_store(&capture_state, ok ? 2 : -1);
    void (*write_overlap_report)(void) =
        (void (*)(void))dlsym(RTLD_DEFAULT, "l16_write_mode8_overlap_report");
    if (write_overlap_report != NULL) write_overlap_report();
    if (getenv("L16_INDEX5_EXIT_AFTER_CAPTURE") != NULL) _exit(ok ? 0 : 70);
}

__attribute__((constructor))
static void install_index5_hook(void) {
    libcp_base = find_libcp_base();
    if (libcp_base == 0) return;
    producer_trampoline = install_hook(0x299c70, 15, (const void *)&producer_hook);
}

__attribute__((destructor))
static void write_capture_status(void) {
    const char *directory = getenv("L16_INDEX5_CAPTURE_DIR");
    if (directory == NULL) return;
    char path[1024];
    snprintf(path, sizeof(path), "%s/status.txt", directory);
    FILE *output = fopen(path, "w");
    if (output == NULL) return;
    fprintf(output, "%d\n", atomic_load(&capture_state));
    fclose(output);
}
