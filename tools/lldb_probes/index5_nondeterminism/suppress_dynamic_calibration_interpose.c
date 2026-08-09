#include <mach-o/dyld.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

typedef void (*copy_fn)(void *, const void *, const void *, const void *, int32_t);

static uintptr_t libcp_base;
static void *copy_trampoline;
static atomic_uint blocked_parent;
static atomic_uint blocked_ba;

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

__attribute__((noinline))
static void copy_hook(void *object, const void *k, const void *rotation,
                      const void *translation, int32_t selector) {
    uintptr_t caller_va = (uintptr_t)__builtin_return_address(0) - libcp_base;
    if (selector == 1 && caller_va == 0x217bc3) {
        atomic_fetch_add(&blocked_parent, 1);
        return;
    }
    if (selector == 1 && caller_va == 0x23d392) {
        atomic_fetch_add(&blocked_ba, 1);
        return;
    }
    ((copy_fn)copy_trampoline)(object, k, rotation, translation, selector);
}

__attribute__((constructor))
static void install_copy_hook(void) {
    libcp_base = find_libcp_base();
    if (libcp_base == 0) return;
    copy_trampoline = install_hook(0xf33d0, 13, (const void *)&copy_hook);
}

__attribute__((destructor))
static void write_suppression_report(void) {
    const char *path = getenv("L16_CALIBRATION_SUPPRESSION_REPORT");
    if (path == NULL) return;
    FILE *output = fopen(path, "w");
    if (output == NULL) return;
    fprintf(output, "blocked_parent=%u\nblocked_ba=%u\n",
            atomic_load(&blocked_parent), atomic_load(&blocked_ba));
    fclose(output);
}
