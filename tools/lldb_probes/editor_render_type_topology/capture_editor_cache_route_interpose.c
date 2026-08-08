#include <mach-o/dyld.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

static uintptr_t libcp_base;
static void *cache_trampoline;
static void *dof_threshold_trampoline;
static void *request_state_trampoline;
static void *quick_select_image_trampoline;
static _Atomic uint64_t total_calls;
static _Atomic uint64_t mode0_dof;
static _Atomic uint64_t mode1_dof;
static _Atomic uint64_t mode2_pipeline;
static _Atomic uint64_t mode4_dof;
static _Atomic uint64_t mode0_pipeline;
static _Atomic uint64_t mode1_pipeline;
static _Atomic uint64_t mode4_pipeline;
static _Atomic uint64_t other_calls;
static _Atomic uint64_t dof_threshold_calls;
static _Atomic uint32_t dof_field_80_bits;
static _Atomic uint32_t dof_field_84_bits;
static _Atomic uint32_t dof_field_88_bits;
static _Atomic uint32_t dof_field_98_bits;
static _Atomic uint32_t dof_field_9c_bits;
static _Atomic uint32_t dof_threshold_bits;
static _Atomic uint64_t mode0_threshold_calls;
static _Atomic uint64_t mode1_threshold_calls;
static _Atomic uint32_t mode0_request_min_bits;
static _Atomic uint32_t mode0_request_max_bits;
static _Atomic uint32_t mode1_request_min_bits;
static _Atomic uint32_t mode1_request_max_bits;
static _Atomic uint64_t request_state_calls[5];
static _Atomic uint32_t mode_color_8c0_bits[5][4];
static _Atomic uint32_t mode_color_8d0_bits[5][4];
static _Atomic uint32_t mode_slider_8e0_bits[5];
static _Atomic uint64_t mode_debug_root[5];
static _Atomic uint64_t mode_debug_size[5];
static _Atomic uint64_t mode3_request_key_mask;
static _Atomic uint64_t mode3_matched_calls;
static _Atomic uint64_t mode3_selected_target_va;
static _Atomic int mode3_key_captured;
static _Atomic int32_t mode3_first_request_key;
static _Atomic uint64_t quick_select_calls;
static _Atomic uint64_t quick_select_pixels;
static _Atomic uint64_t quick_select_nonzero;
static _Atomic uint32_t quick_select_width;
static _Atomic uint32_t quick_select_height;
static _Atomic uint32_t quick_select_stride;
static _Atomic uint32_t quick_select_min;
static _Atomic uint32_t quick_select_max;
static _Atomic int quick_select_dumped;

typedef void (*cache_fn)(void *, void *, void *, void *, int);
typedef float (*dof_threshold_fn)(void *);
typedef void *(*request_state_fn)(void *, void *);
typedef void *(*quick_select_image_fn)(void *);
typedef int (*image_int_fn)(void *);
typedef void *(*image_data_fn)(void *);

static uint32_t float_bits(float value) {
    uint32_t bits;
    memcpy(&bits, &value, sizeof(bits));
    return bits;
}

static void update_positive_float_range(_Atomic uint32_t *minimum,
                                        _Atomic uint32_t *maximum,
                                        uint32_t bits) {
    uint32_t current = atomic_load_explicit(minimum, memory_order_relaxed);
    while ((current == 0 || bits < current) &&
           !atomic_compare_exchange_weak_explicit(minimum, &current, bits,
                                                  memory_order_relaxed,
                                                  memory_order_relaxed)) {}
    current = atomic_load_explicit(maximum, memory_order_relaxed);
    while (bits > current &&
           !atomic_compare_exchange_weak_explicit(maximum, &current, bits,
                                                  memory_order_relaxed,
                                                  memory_order_relaxed)) {}
}

static uintptr_t find_libcp_base(void) {
    for (uint32_t i = 0; i < _dyld_image_count(); ++i) {
        const char *name = _dyld_get_image_name(i);
        if (name != NULL && strstr(name, "/libcp.dylib") != NULL) {
            return (uintptr_t)_dyld_get_image_header(i);
        }
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

__attribute__((noinline))
static void cache_route_hook(void *cache, void *output, void *rectangle,
                             void *request, int index) {
    uintptr_t return_va = (uintptr_t)__builtin_return_address(0) - libcp_base;
    atomic_fetch_add_explicit(&total_calls, 1, memory_order_relaxed);
    switch (return_va) {
        case 0x3bb583: atomic_fetch_add(&mode0_dof, 1); break;
        case 0x3bb5f5: atomic_fetch_add(&mode1_dof, 1); break;
        case 0x3bb625: atomic_fetch_add(&mode2_pipeline, 1); break;
        case 0x3bb7da: atomic_fetch_add(&mode4_dof, 1); break;
        case 0x3bb822: atomic_fetch_add(&mode0_pipeline, 1); break;
        case 0x3bb935: atomic_fetch_add(&mode1_pipeline, 1); break;
        case 0x3bba48: atomic_fetch_add(&mode4_pipeline, 1); break;
        default: atomic_fetch_add(&other_calls, 1); break;
    }
    ((cache_fn)cache_trampoline)(cache, output, rectangle, request, index);
}

__attribute__((noinline))
static float dof_threshold_hook(void *cache) {
    uintptr_t return_va = (uintptr_t)__builtin_return_address(0) - libcp_base;
    float value = ((dof_threshold_fn)dof_threshold_trampoline)(cache);
    atomic_fetch_add_explicit(&dof_threshold_calls, 1, memory_order_relaxed);
    atomic_store_explicit(&dof_field_80_bits,
                          float_bits(*(float *)((uint8_t *)cache + 0x80)),
                          memory_order_relaxed);
    atomic_store_explicit(&dof_field_84_bits,
                          float_bits(*(float *)((uint8_t *)cache + 0x84)),
                          memory_order_relaxed);
    atomic_store_explicit(&dof_field_88_bits,
                          float_bits(*(float *)((uint8_t *)cache + 0x88)),
                          memory_order_relaxed);
    atomic_store_explicit(&dof_field_98_bits,
                          float_bits(*(float *)((uint8_t *)cache + 0x98)),
                          memory_order_relaxed);
    atomic_store_explicit(&dof_field_9c_bits,
                          float_bits(*(float *)((uint8_t *)cache + 0x9c)),
                          memory_order_relaxed);
    atomic_store_explicit(&dof_threshold_bits, float_bits(value),
                          memory_order_relaxed);
    if (return_va == 0x3bb552 || return_va == 0x3bb5c4) {
        void *caller_frame = *(void **)__builtin_frame_address(0);
        uint32_t request_bits = float_bits(
            *(float *)((uint8_t *)caller_frame - 0x4f0));
        if (return_va == 0x3bb552) {
            atomic_fetch_add(&mode0_threshold_calls, 1);
            update_positive_float_range(&mode0_request_min_bits,
                                        &mode0_request_max_bits, request_bits);
        } else {
            atomic_fetch_add(&mode1_threshold_calls, 1);
            update_positive_float_range(&mode1_request_min_bits,
                                        &mode1_request_max_bits, request_bits);
        }
    }
    return value;
}

__attribute__((noinline))
static void *request_state_hook(void *output, void *renderer) {
    uintptr_t return_va = (uintptr_t)__builtin_return_address(0) - libcp_base;
    int expected_mode = -1;
    switch (return_va) {
        case 0x3bb536: expected_mode = 0; break;
        case 0x3bb5a8: expected_mode = 1; break;
        case 0x3bb727: expected_mode = 3; break;
        case 0x3bb78d: expected_mode = 4; break;
        default: break;
    }
    void *result = ((request_state_fn)request_state_trampoline)(output, renderer);
    if (expected_mode >= 0) {
        uint8_t *state = (uint8_t *)renderer;
        atomic_fetch_add_explicit(&request_state_calls[expected_mode], 1,
                                  memory_order_relaxed);
        for (int lane = 0; lane < 4; ++lane) {
            atomic_store_explicit(&mode_color_8c0_bits[expected_mode][lane],
                                  float_bits(*(float *)(state + 0x8c0 + 4 * lane)),
                                  memory_order_relaxed);
            atomic_store_explicit(&mode_color_8d0_bits[expected_mode][lane],
                                  float_bits(*(float *)(state + 0x8d0 + 4 * lane)),
                                  memory_order_relaxed);
        }
        atomic_store_explicit(&mode_slider_8e0_bits[expected_mode],
                              float_bits(*(float *)(state + 0x8e0)),
                              memory_order_relaxed);
        atomic_store_explicit(&mode_debug_root[expected_mode],
                              (uintptr_t)*(void **)(state + 0x6e8),
                              memory_order_relaxed);
        atomic_store_explicit(&mode_debug_size[expected_mode],
                              *(uint64_t *)(state + 0x6f0),
                              memory_order_relaxed);
        if (expected_mode == 3) {
            int key = *(int *)((uint8_t *)output + 0x38);
            int uncaptured = 0;
            if (atomic_compare_exchange_strong_explicit(&mode3_key_captured,
                                                        &uncaptured, 1,
                                                        memory_order_relaxed,
                                                        memory_order_relaxed))
                atomic_store_explicit(&mode3_first_request_key, key,
                                      memory_order_relaxed);
            if (key >= 0 && key < 64)
                atomic_fetch_or_explicit(&mode3_request_key_mask,
                                         UINT64_C(1) << key,
                                         memory_order_relaxed);
            uint8_t *sentinel = state + 0x6e8;
            uint8_t *node = *(uint8_t **)(state + 0x6e8);
            uint8_t *candidate = sentinel;
            while (node != NULL) {
                if (*(int *)(node + 0x20) < key) {
                    node = *(uint8_t **)(node + 0x08);
                } else {
                    candidate = node;
                    node = *(uint8_t **)node;
                }
            }
            if (candidate != sentinel && *(int *)(candidate + 0x20) == key) {
                void *object = *(void **)(candidate + 0x28);
                void **vtable = object == NULL ? NULL : *(void ***)object;
                uintptr_t target = vtable == NULL ? 0 : (uintptr_t)vtable[2];
                atomic_fetch_add_explicit(&mode3_matched_calls, 1,
                                          memory_order_relaxed);
                atomic_store_explicit(&mode3_selected_target_va,
                                      target - libcp_base,
                                      memory_order_relaxed);
            }
        }
    }
    return result;
}

__attribute__((noinline))
static void *quick_select_image_hook(void *editor) {
    void *image = ((quick_select_image_fn)quick_select_image_trampoline)(editor);
    uintptr_t return_va = (uintptr_t)__builtin_return_address(0) - libcp_base;
    if (return_va == 0x3bbf43 && image != NULL) {
        int width = ((image_int_fn)(libcp_base + 0x398010))(image);
        int height = ((image_int_fn)(libcp_base + 0x398020))(image);
        int stride = ((image_int_fn)(libcp_base + 0x398030))(image);
        uint8_t *data = ((image_data_fn)(libcp_base + 0x398000))(image);
        uint64_t nonzero = 0;
        uint32_t minimum = 255;
        uint32_t maximum = 0;
        if (data != NULL && width > 0 && height > 0 && stride >= width) {
            for (int y = 0; y < height; ++y) {
                for (int x = 0; x < width; ++x) {
                    uint32_t value = data[(size_t)y * (size_t)stride + (size_t)x];
                    if (value != 0) ++nonzero;
                    if (value < minimum) minimum = value;
                    if (value > maximum) maximum = value;
                }
            }
        }
        atomic_fetch_add_explicit(&quick_select_calls, 1, memory_order_relaxed);
        atomic_store_explicit(&quick_select_pixels,
                              (uint64_t)(uint32_t)width * (uint64_t)(uint32_t)height,
                              memory_order_relaxed);
        atomic_store_explicit(&quick_select_nonzero, nonzero, memory_order_relaxed);
        atomic_store_explicit(&quick_select_width, (uint32_t)width, memory_order_relaxed);
        atomic_store_explicit(&quick_select_height, (uint32_t)height, memory_order_relaxed);
        atomic_store_explicit(&quick_select_stride, (uint32_t)stride, memory_order_relaxed);
        atomic_store_explicit(&quick_select_min, minimum, memory_order_relaxed);
        atomic_store_explicit(&quick_select_max, maximum, memory_order_relaxed);
        const char *dump_path = getenv("L16_QUICK_SELECT_MASK_OUT");
        int expected = 0;
        if (dump_path != NULL && data != NULL && width > 0 && height > 0 &&
            stride >= width &&
            atomic_compare_exchange_strong_explicit(
                &quick_select_dumped, &expected, 1,
                memory_order_relaxed, memory_order_relaxed)) {
            FILE *dump = fopen(dump_path, "wb");
            if (dump != NULL) {
                for (int y = 0; y < height; ++y)
                    fwrite(data + (size_t)y * (size_t)stride, 1,
                           (size_t)width, dump);
                fclose(dump);
            }
        }
    }
    return image;
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

__attribute__((constructor))
static void install_cache_route_hook(void) {
    libcp_base = find_libcp_base();
    if (libcp_base == 0) return;
    cache_trampoline = install_hook(0x3d0650, 17, (const void *)&cache_route_hook);
    dof_threshold_trampoline = install_hook(0x3f06d0, 20,
                                             (const void *)&dof_threshold_hook);
    request_state_trampoline = install_hook(0x3c6f80, 13,
                                             (const void *)&request_state_hook);
    quick_select_image_trampoline = install_hook(0x3a81e0, 13,
                                                  (const void *)&quick_select_image_hook);
}

__attribute__((destructor))
static void write_cache_route_report(void) {
    const char *path = getenv("L16_CACHE_ROUTE_OUT");
    if (path == NULL) return;
    FILE *output = fopen(path, "w");
    if (output == NULL) return;
    fprintf(output,
            "{\n"
            "  \"total_calls\": %llu,\n"
            "  \"mode0_dof\": %llu,\n"
            "  \"mode1_dof\": %llu,\n"
            "  \"mode2_pipeline\": %llu,\n"
            "  \"mode4_dof\": %llu,\n"
            "  \"mode0_pipeline\": %llu,\n"
            "  \"mode1_pipeline\": %llu,\n"
            "  \"mode4_pipeline\": %llu,\n"
            "  \"other_calls\": %llu,\n"
            "  \"dof_threshold_calls\": %llu,\n"
            "  \"dof_field_80_bits\": \"%08x\",\n"
            "  \"dof_field_84_bits\": \"%08x\",\n"
            "  \"dof_field_88_bits\": \"%08x\",\n"
            "  \"dof_field_98_bits\": \"%08x\",\n"
            "  \"dof_field_9c_bits\": \"%08x\",\n"
            "  \"dof_threshold_bits\": \"%08x\",\n"
            "  \"mode0_threshold_calls\": %llu,\n"
            "  \"mode0_request_min_bits\": \"%08x\",\n"
            "  \"mode0_request_max_bits\": \"%08x\",\n"
            "  \"mode1_threshold_calls\": %llu,\n"
            "  \"mode1_request_min_bits\": \"%08x\",\n"
            "  \"mode1_request_max_bits\": \"%08x\",\n"
            "  \"mode3_request_key_mask\": \"0x%llx\",\n"
            "  \"mode3_first_request_key\": %d,\n"
            "  \"mode3_matched_calls\": %llu,\n"
            "  \"mode3_selected_target_va\": \"0x%llx\",\n"
            "  \"quick_select_mask\": {\"calls\":%llu,\"width\":%u,\"height\":%u,\"stride\":%u,\"pixels\":%llu,\"nonzero\":%llu,\"min\":%u,\"max\":%u},\n"
            "  \"request_state\": [\n"
            "    {\"mode\":0,\"calls\":%llu,\"color_8c0\":[\"%08x\",\"%08x\",\"%08x\",\"%08x\"],\"color_8d0\":[\"%08x\",\"%08x\",\"%08x\",\"%08x\"],\"slider_8e0\":\"%08x\",\"debug_root\":\"0x%llx\",\"debug_size\":%llu},\n"
            "    {\"mode\":1,\"calls\":%llu,\"color_8c0\":[\"%08x\",\"%08x\",\"%08x\",\"%08x\"],\"color_8d0\":[\"%08x\",\"%08x\",\"%08x\",\"%08x\"],\"slider_8e0\":\"%08x\",\"debug_root\":\"0x%llx\",\"debug_size\":%llu},\n"
            "    {\"mode\":2,\"calls\":%llu,\"color_8c0\":[\"%08x\",\"%08x\",\"%08x\",\"%08x\"],\"color_8d0\":[\"%08x\",\"%08x\",\"%08x\",\"%08x\"],\"slider_8e0\":\"%08x\",\"debug_root\":\"0x%llx\",\"debug_size\":%llu},\n"
            "    {\"mode\":3,\"calls\":%llu,\"color_8c0\":[\"%08x\",\"%08x\",\"%08x\",\"%08x\"],\"color_8d0\":[\"%08x\",\"%08x\",\"%08x\",\"%08x\"],\"slider_8e0\":\"%08x\",\"debug_root\":\"0x%llx\",\"debug_size\":%llu},\n"
            "    {\"mode\":4,\"calls\":%llu,\"color_8c0\":[\"%08x\",\"%08x\",\"%08x\",\"%08x\"],\"color_8d0\":[\"%08x\",\"%08x\",\"%08x\",\"%08x\"],\"slider_8e0\":\"%08x\",\"debug_root\":\"0x%llx\",\"debug_size\":%llu}\n"
            "  ]\n"
            "}\n",
            (unsigned long long)atomic_load(&total_calls),
            (unsigned long long)atomic_load(&mode0_dof),
            (unsigned long long)atomic_load(&mode1_dof),
            (unsigned long long)atomic_load(&mode2_pipeline),
            (unsigned long long)atomic_load(&mode4_dof),
            (unsigned long long)atomic_load(&mode0_pipeline),
            (unsigned long long)atomic_load(&mode1_pipeline),
            (unsigned long long)atomic_load(&mode4_pipeline),
            (unsigned long long)atomic_load(&other_calls),
            (unsigned long long)atomic_load(&dof_threshold_calls),
            atomic_load(&dof_field_80_bits),
            atomic_load(&dof_field_84_bits),
            atomic_load(&dof_field_88_bits),
            atomic_load(&dof_field_98_bits),
            atomic_load(&dof_field_9c_bits),
            atomic_load(&dof_threshold_bits),
            (unsigned long long)atomic_load(&mode0_threshold_calls),
            atomic_load(&mode0_request_min_bits),
            atomic_load(&mode0_request_max_bits),
            (unsigned long long)atomic_load(&mode1_threshold_calls),
            atomic_load(&mode1_request_min_bits),
            atomic_load(&mode1_request_max_bits),
            (unsigned long long)atomic_load(&mode3_request_key_mask),
            atomic_load(&mode3_first_request_key),
            (unsigned long long)atomic_load(&mode3_matched_calls),
            (unsigned long long)atomic_load(&mode3_selected_target_va),
            (unsigned long long)atomic_load(&quick_select_calls),
            atomic_load(&quick_select_width), atomic_load(&quick_select_height),
            atomic_load(&quick_select_stride),
            (unsigned long long)atomic_load(&quick_select_pixels),
            (unsigned long long)atomic_load(&quick_select_nonzero),
            atomic_load(&quick_select_min), atomic_load(&quick_select_max),
#define MODE_ARGS(mode) \
            (unsigned long long)atomic_load(&request_state_calls[mode]), \
            atomic_load(&mode_color_8c0_bits[mode][0]), atomic_load(&mode_color_8c0_bits[mode][1]), \
            atomic_load(&mode_color_8c0_bits[mode][2]), atomic_load(&mode_color_8c0_bits[mode][3]), \
            atomic_load(&mode_color_8d0_bits[mode][0]), atomic_load(&mode_color_8d0_bits[mode][1]), \
            atomic_load(&mode_color_8d0_bits[mode][2]), atomic_load(&mode_color_8d0_bits[mode][3]), \
            atomic_load(&mode_slider_8e0_bits[mode]), \
            (unsigned long long)atomic_load(&mode_debug_root[mode]), \
            (unsigned long long)atomic_load(&mode_debug_size[mode])
            MODE_ARGS(0), MODE_ARGS(1), MODE_ARGS(2), MODE_ARGS(3), MODE_ARGS(4));
#undef MODE_ARGS
    fclose(output);
}
