#include <dlfcn.h>
#include <inttypes.h>
#include <mach-o/dyld.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *kLibcp =
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib";

typedef struct {
    int32_t rect[4];
    int32_t width;
    int32_t height;
    int32_t stride;
    int32_t marker;
    float *data;
    void *owner;
} ImageDescriptor;

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

static float *read_floats(const char *path, size_t size) {
    FILE *input = fopen(path, "rb");
    if (input == NULL) {
        perror(path);
        return NULL;
    }
    float *data = aligned_alloc(16, size);
    if (data == NULL || fread(data, 1, size, input) != size) {
        fprintf(stderr, "failed to read %s\n", path);
        free(data);
        data = NULL;
    }
    fclose(input);
    return data;
}

static int write_descriptor(const char *path, const ImageDescriptor *image,
                            size_t size) {
    FILE *output = fopen(path, "wb");
    if (output == NULL) {
        perror(path);
        return 0;
    }
    int ok = fwrite(image->data, 1, size, output) == size;
    fclose(output);
    return ok;
}

static ImageDescriptor source_descriptor(float *data, int width, int height) {
    ImageDescriptor image = {
        .rect = {0, 0, width, height},
        .width = width,
        .height = height,
        .stride = width,
        .marker = -1,
        .data = data,
        .owner = data,
    };
    return image;
}

int main(int argc, char **argv) {
    if (argc != 5) {
        fprintf(stderr, "usage: %s input_rgb.raw output_rgb.raw input_hsv.raw output_hsv.raw\n",
                argv[0]);
        return 2;
    }
    void *handle = dlopen(kLibcp, RTLD_NOW | RTLD_LOCAL);
    uintptr_t base = find_libcp_base();
    if (handle == NULL || base == 0) {
        fprintf(stderr, "failed to load libcp: %s\n", dlerror());
        return 1;
    }
    enum { kWidth = 652, kHeight = 489, kLanes = 4 };
    const size_t size = (size_t)kWidth * kHeight * kLanes * sizeof(float);
    float *input_rgb = read_floats(argv[1], size);
    float *output_rgb = read_floats(argv[2], size);
    if (input_rgb == NULL || output_rgb == NULL) {
        return 1;
    }
    ImageDescriptor input = source_descriptor(input_rgb, kWidth, kHeight);
    ImageDescriptor output = source_descriptor(output_rgb, kWidth, kHeight);
    ImageDescriptor input_hsv = {0};
    ImageDescriptor output_hsv = {0};
    typedef void *(*image_convert_fn)(ImageDescriptor *, const ImageDescriptor *);
    typedef void (*image_destroy_fn)(ImageDescriptor *);
    image_convert_fn rgb_to_hsv = (image_convert_fn)(base + 0xaa790);
    image_destroy_fn destroy = (image_destroy_fn)(base + 0xf4e0);

    rgb_to_hsv(&input_hsv, &input);
    rgb_to_hsv(&output_hsv, &output);
    int ok = input_hsv.data != NULL && output_hsv.data != NULL &&
             write_descriptor(argv[3], &input_hsv, size) &&
             write_descriptor(argv[4], &output_hsv, size);
    printf("libcp_base=0x%" PRIxPTR " rgb_to_hsv=0xaa790\n", base);
    printf("input_hsv=%g,%g,%g,%g output_hsv=%g,%g,%g,%g\n",
           input_hsv.data[0], input_hsv.data[1], input_hsv.data[2],
           input_hsv.data[3], output_hsv.data[0], output_hsv.data[1],
           output_hsv.data[2], output_hsv.data[3]);
    printf("dump_size=%zu status=%s\n", size, ok ? "ok" : "failed");

    destroy(&output_hsv);
    destroy(&input_hsv);
    free(output_rgb);
    free(input_rgb);
    dlclose(handle);
    return ok ? 0 : 1;
}
