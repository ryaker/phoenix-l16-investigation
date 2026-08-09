#include <mach-o/dyld.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

typedef void (*copy_fn)(void *, const void *, const void *, const void *, int32_t);

static uintptr_t libcp_base;
static void *copy_trampoline;
static pthread_mutex_t report_mutex = PTHREAD_MUTEX_INITIALIZER;
static uint32_t sequence;

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

static void append_packet(uintptr_t caller, const void *object) {
    const char *path = getenv("L16_CURRENT_BANK_WRITE_REPORT");
    if (path == NULL || object == NULL) return;
    uint64_t caller_va = caller - libcp_base;
    uint32_t camera_id;
    uint8_t current[0x54];
    memcpy(&camera_id, (const uint8_t *)object + 0x60, sizeof(camera_id));
    memcpy(current, (const uint8_t *)object + 0x12c, sizeof(current));

    pthread_mutex_lock(&report_mutex);
    FILE *output = fopen(path, "ab");
    if (output != NULL) {
        uint32_t packet_sequence = sequence++;
        fwrite(&packet_sequence, sizeof(packet_sequence), 1, output);
        fwrite(&camera_id, sizeof(camera_id), 1, output);
        fwrite(&caller_va, sizeof(caller_va), 1, output);
        fwrite(current, sizeof(current), 1, output);
        fclose(output);
    }
    pthread_mutex_unlock(&report_mutex);
}

__attribute__((noinline))
static void copy_hook(void *object, const void *k, const void *rotation,
                      const void *translation, int32_t selector) {
    uintptr_t caller = (uintptr_t)__builtin_return_address(0);
    ((copy_fn)copy_trampoline)(object, k, rotation, translation, selector);
    if (selector == 1) append_packet(caller, object);
}

__attribute__((constructor))
static void install_copy_hook(void) {
    libcp_base = find_libcp_base();
    if (libcp_base == 0) return;
    copy_trampoline = install_hook(0xf33d0, 13, (const void *)&copy_hook);
}
