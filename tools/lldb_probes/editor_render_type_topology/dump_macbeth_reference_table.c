#include <dlfcn.h>
#include <inttypes.h>
#include <mach-o/dyld.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static const char *kLibcp =
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib";

typedef struct {
    float lane[3];
} Vec3f;

typedef struct {
    Vec3f *begin;
    Vec3f *end;
    Vec3f *capacity;
} Vec3Vector;

static uintptr_t find_libcp_base(void) {
    for (uint32_t i = 0; i < _dyld_image_count(); ++i) {
        const char *name = _dyld_get_image_name(i);
        if (name != NULL && strstr(name, "/libcp.dylib") != NULL) {
            return (uintptr_t)_dyld_get_image_header(i);
        }
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr,
                "usage: %s embedded_reference.raw converted_target.raw roundtrip_xyz.raw\n",
                argv[0]);
        return 2;
    }
    void *handle = dlopen(kLibcp, RTLD_NOW | RTLD_LOCAL);
    uintptr_t base = find_libcp_base();
    if (handle == NULL || base == 0) {
        fprintf(stderr, "failed to load libcp: %s\n", dlerror());
        return 1;
    }

    const Vec3Vector *reference = (const Vec3Vector *)(base + 0x66dfa0);
    ptrdiff_t count = reference->end - reference->begin;
    unsigned char base_config[0x10] __attribute__((aligned(16))) = {0};
    unsigned char input_config[0x48] __attribute__((aligned(16))) = {0};
    unsigned char output_config[0x48] __attribute__((aligned(16))) = {0};
    typedef void (*illuminant_init_fn)(void *, int);
    typedef void (*color_config_init_fn)(void *, int, const void *, int);
    typedef void (*convert_patches_fn)(Vec3Vector *, const Vec3Vector *,
                                       const void *, const void *, int);
    illuminant_init_fn illuminant_init = (illuminant_init_fn)(base + 0xa9910);
    color_config_init_fn color_config_init =
        (color_config_init_fn)(base + 0xa9ea0);
    convert_patches_fn convert_patches = (convert_patches_fn)(base + 0xaa500);
    illuminant_init(base_config, 5);
    color_config_init(input_config, 7, base_config, 1);
    memset(base_config, 0, sizeof(base_config));
    illuminant_init(base_config, 5);
    color_config_init(output_config, 8, base_config, 1);
    Vec3Vector target = {0};
    convert_patches(&target, reference, input_config, output_config, 1);
    ptrdiff_t target_count = target.end - target.begin;
    Vec3Vector roundtrip = {0};
    convert_patches(&roundtrip, &target, output_config, input_config, 1);
    ptrdiff_t roundtrip_count = roundtrip.end - roundtrip.begin;

    FILE *raw = fopen(argv[1], "wb");
    size_t raw_size = (size_t)count * sizeof(Vec3f);
    if (raw == NULL || fwrite(reference->begin, 1, raw_size, raw) != raw_size) {
        perror(argv[1]);
        return 1;
    }
    fclose(raw);
    raw = fopen(argv[3], "wb");
    size_t roundtrip_size = (size_t)roundtrip_count * sizeof(Vec3f);
    if (raw == NULL ||
        fwrite(roundtrip.begin, 1, roundtrip_size, raw) != roundtrip_size) {
        perror(argv[3]);
        return 1;
    }
    fclose(raw);
    raw = fopen(argv[2], "wb");
    size_t target_size = (size_t)target_count * sizeof(Vec3f);
    if (raw == NULL || fwrite(target.begin, 1, target_size, raw) != target_size) {
        perror(argv[2]);
        return 1;
    }
    fclose(raw);
    printf("{\n  \"libcp_base\": \"0x%" PRIxPTR "\",\n", base);
    printf("  \"vector_va\": \"0x66dfa0\",\n");
    printf("  \"count\": %td,\n  \"embedded_reference_patches\": [\n", count);
    for (ptrdiff_t i = 0; i < count; ++i) {
        const Vec3f *patch = &reference->begin[i];
        printf("    [%.9g, %.9g, %.9g]%s\n", patch->lane[0], patch->lane[1],
               patch->lane[2], i + 1 == count ? "" : ",");
    }
    printf("  ],\n  \"converted_target_count\": %td,\n", target_count);
    printf("  \"converted_target_patches\": [\n");
    for (ptrdiff_t i = 0; i < target_count; ++i) {
        const Vec3f *patch = &target.begin[i];
        printf("    [%.9g, %.9g, %.9g]%s\n", patch->lane[0], patch->lane[1],
               patch->lane[2], i + 1 == target_count ? "" : ",");
    }
    printf("  ],\n  \"roundtrip_xyz_count\": %td,\n", roundtrip_count);
    printf("  \"roundtrip_xyz_patches\": [\n");
    for (ptrdiff_t i = 0; i < roundtrip_count; ++i) {
        const Vec3f *patch = &roundtrip.begin[i];
        printf("    [%.9g, %.9g, %.9g]%s\n", patch->lane[0], patch->lane[1],
               patch->lane[2], i + 1 == roundtrip_count ? "" : ",");
    }
    printf("  ]\n}\n");
    dlclose(handle);
    return count == 24 && target_count == 24 && roundtrip_count == 24 ? 0 : 1;
}
