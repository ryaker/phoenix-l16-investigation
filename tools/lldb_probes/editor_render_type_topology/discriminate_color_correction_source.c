#include <dlfcn.h>
#include <inttypes.h>
#include <mach-o/dyld.h>
#include <math.h>
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

static void *read_file(const char *path, size_t expected_size) {
    FILE *input = fopen(path, "rb");
    if (input == NULL) {
        perror(path);
        return NULL;
    }
    void *data = aligned_alloc(16, expected_size);
    if (data == NULL || fread(data, 1, expected_size, input) != expected_size) {
        fprintf(stderr, "failed to read %s\n", path);
        free(data);
        data = NULL;
    }
    fclose(input);
    return data;
}

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s input.raw expected.raw\n", argv[0]);
        return 2;
    }
    void *handle = dlopen(kLibcp, RTLD_NOW | RTLD_LOCAL);
    uintptr_t base = find_libcp_base();
    if (handle == NULL || base == 0) {
        fprintf(stderr, "failed to load libcp: %s\n", dlerror());
        return 1;
    }

    enum { kWidth = 652, kHeight = 489, kLanes = 4 };
    const size_t count = (size_t)kWidth * kHeight * kLanes;
    const size_t size = count * sizeof(float);
    float *source = read_file(argv[1], size);
    float *expected = read_file(argv[2], size);
    float *destination = aligned_alloc(16, size);
    if (source == NULL || expected == NULL || destination == NULL) {
        return 1;
    }

    typedef void (*color_space_init_fn)(void *, int);
    typedef void (*color_config_init_fn)(void *, int, const void *, int);
    typedef const void *(*converter_select_fn)(int, int);
    typedef void (*adaptation_matrix_fn)(float *, const void *, const void *, int);
    typedef void (*converter_fn)(float *, const float *, int, int, int, int,
                                 const void *, const void *, const float *);
    color_space_init_fn color_space_init =
        (color_space_init_fn)(base + 0xa9910);
    color_config_init_fn color_config_init =
        (color_config_init_fn)(base + 0xa9ea0);
    converter_select_fn converter_select =
        (converter_select_fn)(base + 0xaa110);
    adaptation_matrix_fn adaptation_matrix =
        (adaptation_matrix_fn)(base + 0xa9340);

    uint8_t destination_space[12] = {0};
    uint8_t destination_config[52] = {0};
    color_space_init(destination_space, 5);
    color_config_init(destination_config, 5, destination_space, 1);

    for (int source_selector = 2; source_selector <= 6; ++source_selector) {
        uint8_t source_space[12] = {0};
        uint8_t source_config[52] = {0};
        float adaptation[9] __attribute__((aligned(16))) = {0};
        color_space_init(source_space, source_selector);
        color_config_init(source_config, source_selector, source_space, 1);
        adaptation_matrix(adaptation, source_config + 0x24,
                          destination_config + 0x24, 1);
        const void *converter = converter_select(source_selector, 5);
        memset(destination, 0, size);
        ((converter_fn)converter)(destination, source, kWidth, kHeight,
                                  kWidth, kWidth, source_config,
                                  destination_config, adaptation);

        double squared = 0.0;
        double absolute = 0.0;
        float maximum = 0.0f;
        size_t exact = 0;
        size_t rgb_count = 0;
        size_t alpha_exact = 0;
        for (size_t i = 0; i < count; ++i) {
            if ((i & 3) == 3) {
                alpha_exact += destination[i] == expected[i];
                continue;
            }
            float difference = destination[i] - expected[i];
            float magnitude = fabsf(difference);
            squared += (double)difference * difference;
            absolute += magnitude;
            if (magnitude > maximum) {
                maximum = magnitude;
            }
            exact += destination[i] == expected[i];
            ++rgb_count;
        }
        printf("source=%d converter=0x%" PRIxPTR
               " rgb_exact=%zu/%zu alpha_exact=%zu/%d"
               " mean_abs=%.17g rms=%.17g max=%.17g first=%.9g,%.9g,%.9g,%.9g\n",
               source_selector, (uintptr_t)converter - base, exact, rgb_count,
               alpha_exact, kWidth * kHeight, absolute / rgb_count,
               sqrt(squared / rgb_count), maximum, destination[0],
               destination[1], destination[2], destination[3]);
    }

    free(destination);
    free(expected);
    free(source);
    dlclose(handle);
    return 0;
}
