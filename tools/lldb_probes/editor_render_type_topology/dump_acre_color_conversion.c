#include <dlfcn.h>
#include <inttypes.h>
#include <mach-o/dyld.h>
#include <stdint.h>
#include <stdio.h>
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

    typedef const void *(*default_config_fn)(void);
    typedef const void *(*converter_select_fn)(int, int);
    typedef void (*adaptation_matrix_fn)(float *, const void *, const void *, int);
    typedef void (*converter_fn)(float *, const float *, int, int, int, int,
                                 const void *, const void *, const float *);

    default_config_fn default_config = (default_config_fn)(base + 0x2d6cd0);
    converter_select_fn converter_select = (converter_select_fn)(base + 0xaa110);
    adaptation_matrix_fn adaptation_matrix =
        (adaptation_matrix_fn)(base + 0xa9340);

    static const uint8_t source_config[52] = {
        0x7c, 0x2d, 0xd3, 0x3e, 0x37, 0x14, 0xb7, 0x3e,
        0x9c, 0xc4, 0x38, 0x3e, 0xed, 0xc6, 0x59, 0x3e,
        0x37, 0x14, 0x37, 0x3f, 0x7d, 0xd0, 0x93, 0x3d,
        0x21, 0x62, 0x9e, 0x3c, 0xef, 0x1a, 0xf4, 0x3d,
        0x21, 0x47, 0x73, 0x3f, 0xb4, 0x1d, 0xa0, 0x3e,
        0xb8, 0x75, 0xa8, 0x3e, 0x07, 0x00, 0x00, 0x00,
        0x02, 0x00, 0x00, 0x00,
    };
    const uint8_t *destination_config = default_config();
    const void *converter = converter_select(5, 2);
    float adaptation[9] __attribute__((aligned(16))) = {0};
    adaptation_matrix(adaptation, destination_config + 0x24,
                      source_config + 0x24, 1);

    float source[12] __attribute__((aligned(16))) = {
        0.0f, 0.003f, 0.04045f, 1.0f,
        0.18f, 0.5f, 1.0f, 0.75f,
        1.25f, -0.25f, 2.0f, 0.5f,
    };
    float destination[12] __attribute__((aligned(16))) = {0};
    ((converter_fn)converter)(destination, source, 3, 1, 3, 3,
                              destination_config, source_config, adaptation);

    printf("libcp_base=0x%" PRIxPTR "\n", base);
    printf("converter_5_2=0x%" PRIxPTR "\n", (uintptr_t)converter - base);
    print_hex("source_config", source_config, sizeof(source_config));
    print_hex("destination_config", destination_config, 52);
    print_hex("adaptation", adaptation, sizeof(adaptation));
    print_hex("source", source, sizeof(source));
    print_hex("destination", destination, sizeof(destination));

    dlclose(handle);
    return 0;
}
