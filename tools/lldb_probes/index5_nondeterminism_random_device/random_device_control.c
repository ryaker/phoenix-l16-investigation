#include <mach-o/dyld.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

/* libcp's lazy pointer for std::__1::random_device::operator()(). */
static const uintptr_t random_device_got_va = 0x64fc20;

static atomic_uint call_count;
static atomic_flag report_lock = ATOMIC_FLAG_INIT;
static uint32_t fixed_seed = 0x12345678U;
static uintptr_t libcp_base;
static uintptr_t original_target;

static void write_random_device_report(void);

static uintptr_t find_libcp_base(void) {
    for (uint32_t i = 0; i < _dyld_image_count(); ++i) {
        const char *name = _dyld_get_image_name(i);
        if (name != NULL && strstr(name, "/libcp.dylib") != NULL)
            return (uintptr_t)_dyld_get_image_header(i);
    }
    return 0;
}

static void make_writable(void *address) {
    long page_size = sysconf(_SC_PAGESIZE);
    uintptr_t page = (uintptr_t)address & ~((uintptr_t)page_size - 1);
    if (mprotect((void *)page, (size_t)page_size,
                 PROT_READ | PROT_WRITE) != 0)
        abort();
}

static uint32_t controlled_random_device(void *object) {
    (void)object;
    atomic_fetch_add_explicit(&call_count, 1U, memory_order_relaxed);
    while (atomic_flag_test_and_set_explicit(&report_lock, memory_order_acquire)) {}
    write_random_device_report();
    atomic_flag_clear_explicit(&report_lock, memory_order_release);
    return fixed_seed;
}

__attribute__((constructor))
static void install_random_device_control(void) {
    const char *seed_text = getenv("L16_RANDOM_DEVICE_SEED");
    if (seed_text != NULL) fixed_seed = (uint32_t)strtoul(seed_text, NULL, 0);
    libcp_base = find_libcp_base();
    if (libcp_base == 0) return;
    uintptr_t *slot = (uintptr_t *)(libcp_base + random_device_got_va);
    original_target = *slot;
    make_writable(slot);
    *slot = (uintptr_t)&controlled_random_device;
    write_random_device_report();
}

__attribute__((destructor))
static void write_random_device_report(void) {
    const char *path = getenv("L16_RANDOM_DEVICE_REPORT");
    if (path == NULL) return;
    FILE *output = fopen(path, "w");
    if (output == NULL) return;
    fprintf(output,
            "{\n"
            "  \"fixed_seed\": %u,\n"
            "  \"call_count\": %u,\n"
            "  \"libcp_base\": \"0x%llx\",\n"
            "  \"got_va\": \"0x%llx\",\n"
            "  \"original_target\": \"0x%llx\"\n"
            "}\n",
            fixed_seed, atomic_load_explicit(&call_count, memory_order_relaxed),
            (unsigned long long)libcp_base,
            (unsigned long long)random_device_got_va,
            (unsigned long long)original_target);
    fclose(output);
}
