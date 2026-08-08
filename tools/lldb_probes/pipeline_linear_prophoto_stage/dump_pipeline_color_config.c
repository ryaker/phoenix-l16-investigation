#include <dlfcn.h>
#include <inttypes.h>
#include <mach-o/dyld.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *kLibcp =
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib";

static uintptr_t find_libcp_base(void) {
    uint32_t count = _dyld_image_count();
    for (uint32_t i = 0; i < count; ++i) {
        const char *name = _dyld_get_image_name(i);
        if (name != NULL && strstr(name, "/libcp.dylib") != NULL) {
            return (uintptr_t)_dyld_get_image_header(i);
        }
    }
    return 0;
}

static void print_hex(const char *name, const void *value, size_t size) {
    const uint8_t *bytes = value;
    printf("%s=", name);
    for (size_t i = 0; i < size; ++i) {
        printf("%02x", bytes[i]);
    }
    putchar('\n');
}

int main(void) {
    void *handle = dlopen(kLibcp, RTLD_NOW | RTLD_LOCAL);
    if (handle == NULL) {
        fprintf(stderr, "dlopen failed: %s\n", dlerror());
        return 1;
    }

    uintptr_t base = find_libcp_base();
    if (base == 0) {
        fputs("libcp image base not found\n", stderr);
        return 1;
    }

    typedef void (*color_space_init_fn)(void *, int);
    typedef void (*color_config_init_fn)(void *, int, const void *, int);
    typedef const void *(*default_config_fn)(void);
    typedef const void *(*converter_select_fn)(int, int);
    typedef void (*adaptation_matrix_fn)(float *, const void *, const void *, int);
    typedef void (*converter_fn)(float *, const float *, int, int, int, int,
                                 const void *, const void *, const float *);

    color_space_init_fn color_space_init =
        (color_space_init_fn)(base + 0xa9910);
    color_config_init_fn color_config_init =
        (color_config_init_fn)(base + 0xa9ea0);
    default_config_fn default_config =
        (default_config_fn)(base + 0x2d6cd0);
    converter_select_fn converter_select =
        (converter_select_fn)(base + 0xaa110);
    adaptation_matrix_fn adaptation_matrix =
        (adaptation_matrix_fn)(base + 0xa9340);

    uint8_t color_space[12] = {0};
    uint8_t constructed[52] = {0};
    color_space_init(color_space, 5);
    color_config_init(constructed, 5, color_space, 1);
    const void *singleton = default_config();
    const void *converter = converter_select(5, 5);
    float adaptation[9] __attribute__((aligned(16))) = {0};
    adaptation_matrix(adaptation, (const uint8_t *)singleton + 0x24,
                      (const uint8_t *)singleton + 0x24, 1);

    float source[8] __attribute__((aligned(16))) = {
        -0.25f, 0.0f, 1.25f, 0.5f,
        4.0f, -2.0f, 0.125f, 1.0f,
    };
    float destination[8] __attribute__((aligned(16))) = {0};
    ((converter_fn)converter)(destination, source, 2, 1, 2, 2,
                              singleton, singleton, adaptation);

    printf("libcp_base=0x%" PRIxPTR "\n", base);
    print_hex("color_space", color_space, sizeof(color_space));
    print_hex("constructed_config", constructed, sizeof(constructed));
    print_hex("singleton_config", singleton, sizeof(constructed));
    printf("match=%d\n", memcmp(constructed, singleton, sizeof(constructed)) == 0);
    printf("converter_5_5=0x%" PRIxPTR "\n", (uintptr_t)converter - base);
    print_hex("adaptation", adaptation, sizeof(adaptation));
    print_hex("source", source, sizeof(source));
    print_hex("destination", destination, sizeof(destination));
    printf("pixel_match=%d\n", memcmp(source, destination, sizeof(source)) == 0);

    dlclose(handle);
    return 0;
}
