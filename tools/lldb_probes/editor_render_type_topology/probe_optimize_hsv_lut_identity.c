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
    void *begin;
    void *end;
    void *capacity;
} Vector;

typedef struct {
    float matrix[9];
    uint32_t padding;
    void *map;
    void *map_control;
} OptimizerResult;

typedef struct {
    int32_t hue_divisions;
    int32_t saturation_divisions;
    int32_t value_divisions;
    uint32_t padding;
    Vector cells;
} HSVMap;

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
    if (argc != 3) {
        fprintf(stderr, "usage: %s source_macbeth.raw map.raw\n", argv[0]);
        return 2;
    }
    void *handle = dlopen(kLibcp, RTLD_NOW | RTLD_LOCAL);
    uintptr_t base = find_libcp_base();
    if (handle == NULL || base == 0) {
        fprintf(stderr, "failed to load libcp: %s\n", dlerror());
        return 1;
    }

    const Vector *reference = (const Vector *)(base + 0x66dfa0);
    Vec3f source_patches[24];
    FILE *source_file = fopen(argv[1], "rb");
    if (source_file == NULL ||
        fread(source_patches, sizeof(source_patches), 1, source_file) != 1) {
        perror(argv[1]);
        return 1;
    }
    fclose(source_file);
    Vector source = {source_patches, source_patches + 24, source_patches + 24};
    unsigned char base_config[0x10] __attribute__((aligned(16))) = {0};
    unsigned char source_config[0x48] __attribute__((aligned(16))) = {0};
    unsigned char target_config[0x48] __attribute__((aligned(16))) = {0};
    typedef void (*illuminant_init_fn)(void *, int);
    typedef void (*color_config_init_fn)(void *, int, const void *, int);
    typedef void (*convert_patches_fn)(Vector *, const Vector *, const void *,
                                       const void *, int);
    illuminant_init_fn illuminant_init = (illuminant_init_fn)(base + 0xa9910);
    color_config_init_fn color_config_init =
        (color_config_init_fn)(base + 0xa9ea0);
    convert_patches_fn convert_patches = (convert_patches_fn)(base + 0xaa500);

    illuminant_init(base_config, 5);
    color_config_init(source_config, 7, base_config, 1);
    memset(base_config, 0, sizeof(base_config));
    illuminant_init(base_config, 5);
    color_config_init(target_config, 8, base_config, 1);
    Vector reference_target = {0};
    convert_patches(&reference_target, reference, source_config, target_config, 1);
    if ((uint8_t *)reference_target.end - (uint8_t *)reference_target.begin !=
        24 * sizeof(Vec3f)) {
        fprintf(stderr, "reference conversion returned the wrong patch count\n");
        return 1;
    }

    float weights[24];
    for (size_t i = 0; i < 24; ++i) {
        weights[i] = 1.0f;
    }
    Vector weight_vector = {weights, weights + 24, weights + 24};
    unsigned char illuminant[0x48] __attribute__((aligned(16))) = {0};
    illuminant_init(illuminant, 5);

    OptimizerResult result = {0};
    typedef void (*optimizer_fn)(OptimizerResult *, const Vector *, const Vector *,
                                 const void *, const Vector *, void *);
    optimizer_fn optimize = (optimizer_fn)(base + 0x116ee0);
    optimize(&result, &source, &reference_target, illuminant, &weight_vector, NULL);

    unsigned char calibration[0xa0] __attribute__((aligned(16))) = {0};
    memcpy(calibration + 0x60, &source, sizeof(source));
    typedef void (*calibration_build_fn)(void *);
    calibration_build_fn calibration_build =
        (calibration_build_fn)(base + 0x113230);
    calibration_build(calibration);

    HSVMap *manual_map = (HSVMap *)result.map;
    HSVMap *map = NULL;
    memcpy(&map, calibration + 0x90, sizeof(map));
    if (map == NULL) {
        fprintf(stderr, "calibration wrapper returned a null map\n");
        return 1;
    }
    size_t cell_bytes = (uint8_t *)map->cells.end - (uint8_t *)map->cells.begin;
    size_t manual_cell_bytes = manual_map == NULL ? 0 :
        (size_t)((uint8_t *)manual_map->cells.end -
                 (uint8_t *)manual_map->cells.begin);
    int manual_equal = manual_cell_bytes == cell_bytes &&
        memcmp(manual_map->cells.begin, map->cells.begin, cell_bytes) == 0;
    FILE *output = fopen(argv[2], "wb");
    if (output == NULL || fwrite(map->cells.begin, 1, cell_bytes, output) != cell_bytes) {
        perror(argv[2]);
        return 1;
    }
    fclose(output);

    printf("{\n  \"libcp_base\": \"0x%" PRIxPTR "\",\n", base);
    printf("  \"illuminant_prefix_words\": [");
    for (size_t i = 0; i < 6; ++i) {
        uint32_t word;
        memcpy(&word, illuminant + i * sizeof(word), sizeof(word));
        printf("\"0x%08x\"%s", word, i == 5 ? "" : ", ");
    }
    printf("],\n  \"matrix\": [");
    for (size_t i = 0; i < 9; ++i) {
        float value;
        memcpy(&value, calibration + 0xc + i * sizeof(value), sizeof(value));
        printf("%.9g%s", value, i == 8 ? "" : ", ");
    }
    printf("],\n  \"matrix_words\": [");
    for (size_t i = 0; i < 9; ++i) {
        uint32_t word;
        memcpy(&word, calibration + 0xc + i * sizeof(word), sizeof(word));
        printf("\"0x%08x\"%s", word, i == 8 ? "" : ", ");
    }
    printf("],\n  \"optimizer_matrix\": [");
    for (size_t i = 0; i < 9; ++i) {
        printf("%.9g%s", result.matrix[i], i == 8 ? "" : ", ");
    }
    printf("],\n  \"optimizer_matrix_words\": [");
    for (size_t i = 0; i < 9; ++i) {
        uint32_t word;
        memcpy(&word, &result.matrix[i], sizeof(word));
        printf("\"0x%08x\"%s", word, i == 8 ? "" : ", ");
    }
    printf("],\n  \"map_dimensions\": [%d, %d, %d],\n",
           map->hue_divisions, map->saturation_divisions, map->value_divisions);
    printf("  \"manual_optimizer_matches_wrapper\": %s,\n",
           manual_equal ? "true" : "false");
    printf("  \"map_cell_bytes\": %zu,\n", cell_bytes);
    printf("  \"map_cell_count\": %zu\n}\n", cell_bytes / 16);
    int valid = map->hue_divisions == 32 && map->saturation_divisions == 32 &&
                map->value_divisions == 1 && cell_bytes == 1089 * 16;
    dlclose(handle);
    return valid ? 0 : 1;
}
