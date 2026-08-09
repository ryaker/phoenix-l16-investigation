#include <mach-o/dyld.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

typedef void (*executor_fn)(void *, int32_t, int32_t, void *, void *);
typedef void (*index_callback_fn)(void *, const int32_t *, const int32_t *);

static uintptr_t libcp_base;
static void *executor_trampoline;
static atomic_uint serial_calls;

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

static void write_report(void) {
    const char *path = getenv("L16_EXECUTOR_SERIAL_REPORT");
    if (path == NULL) return;
    FILE *output = fopen(path, "w");
    if (output == NULL) return;
    fprintf(output, "serial_calls=%u\n", atomic_load(&serial_calls));
    fclose(output);
}

__attribute__((noinline))
static void executor_hook(void *executor, int32_t begin, int32_t end,
                          void *range_callback, void *index_callback) {
    if (range_callback != NULL || index_callback == NULL) {
        ((executor_fn)executor_trampoline)(executor, begin, end,
                                           range_callback, index_callback);
        return;
    }

    void *callable = *(void **)((uint8_t *)index_callback + 0x20);
    if (callable == NULL) abort();
    void **vtable = *(void ***)callable;
    index_callback_fn invoke = (index_callback_fn)vtable[6];
    const int32_t zero = 0;
    for (int32_t index = begin; index < end; ++index)
        invoke(callable, &index, &zero);
    atomic_fetch_add(&serial_calls, 1);
    write_report();
}

__attribute__((constructor))
static void install_executor_hook(void) {
    libcp_base = find_libcp_base();
    if (libcp_base == 0) return;
    executor_trampoline = install_hook(0x2d30, 12, (const void *)&executor_hook);
}
