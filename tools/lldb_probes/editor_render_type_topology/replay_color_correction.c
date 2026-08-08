#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    float lane[4];
} Vec4;

static void *read_file(const char *path, size_t size) {
    FILE *input = fopen(path, "rb");
    if (input == NULL) {
        perror(path);
        return NULL;
    }
    void *data = aligned_alloc(16, size);
    if (data == NULL || fread(data, 1, size, input) != size) {
        fprintf(stderr, "failed to read %s\n", path);
        free(data);
        data = NULL;
    }
    fclose(input);
    return data;
}

static float clampf(float value, float low, float high) {
    return fminf(fmaxf(value, low), high);
}

static Vec4 rgb_to_hsv(Vec4 rgb) {
    float r = fmaxf(rgb.lane[0], 0.0f);
    float g = fmaxf(rgb.lane[1], 0.0f);
    float b = fmaxf(rgb.lane[2], 0.0f);
    float maximum = fmaxf(fmaxf(r, g), b);
    Vec4 hsv = {{0.0f, 0.0f, maximum, rgb.lane[3]}};
    if (maximum == 0.0f) {
        return hsv;
    }
    float minimum = fminf(fminf(r, g), b);
    float delta = maximum - minimum;
    float saturation = delta / maximum;
    if (saturation == 0.0f) {
        return hsv;
    }
    float inverse_delta = 1.0f / delta;
    float hue;
    if (r == maximum) {
        hue = (g - b) * inverse_delta;
    } else if (g == maximum) {
        hue = (b - r) * inverse_delta + 2.0f;
    } else {
        hue = (r - g) * inverse_delta + 4.0f;
    }
    hue *= 0.1666666716337204f;
    if (hue < 0.0f) {
        hue += 1.0f;
    }
    hsv.lane[0] = hue;
    hsv.lane[1] = saturation;
    return hsv;
}

static Vec4 apply_map(Vec4 hsv, const Vec4 *map, int hue_divisions,
                      int saturation_divisions) {
    float hue_coordinate = clampf(
        hsv.lane[0] * (float)(hue_divisions - 1),
        0.0f, (float)(hue_divisions - 1));
    float saturation_coordinate = clampf(
        hsv.lane[1] * (float)(saturation_divisions - 1),
        0.0f, (float)(saturation_divisions - 1));
    int hue_index = (int)hue_coordinate;
    int saturation_index = (int)saturation_coordinate;
    float hue_fraction = hue_coordinate - floorf(hue_coordinate);
    float saturation_fraction =
        saturation_coordinate - floorf(saturation_coordinate);
    int stride = hue_divisions + 1;
    int index = saturation_index * stride + hue_index;
    Vec4 interpolated;
    for (int lane = 0; lane < 4; ++lane) {
        float lower = map[index].lane[lane] +
            hue_fraction * (map[index + 1].lane[lane] - map[index].lane[lane]);
        float upper_delta =
            (map[index + stride + 1].lane[lane] -
             map[index + stride].lane[lane]) * hue_fraction;
        float vertical = map[index + stride].lane[lane] - lower + upper_delta;
        interpolated.lane[lane] =
            lower + saturation_fraction * vertical;
    }
    Vec4 result = {{
        hsv.lane[0] + interpolated.lane[0],
        hsv.lane[1] * interpolated.lane[1],
        hsv.lane[2] * interpolated.lane[2],
        hsv.lane[3],
    }};
    result.lane[0] -= floorf(result.lane[0]);
    result.lane[0] = clampf(result.lane[0], 0.0f, 1.0f);
    result.lane[1] = clampf(result.lane[1], 0.0f, 1.0f);
    return result;
}

static Vec4 hsv_to_rgb(Vec4 hsv) {
    float six_hue = hsv.lane[0] * 6.0f;
    float red_triangle = clampf(fabsf(six_hue - 3.0f) - 1.0f, 0.0f, 1.0f);
    float green_triangle = clampf(2.0f - fabsf(six_hue - 2.0f), 0.0f, 1.0f);
    float blue_triangle = clampf(2.0f - fabsf(six_hue - 4.0f), 0.0f, 1.0f);
    Vec4 result = {{
        ((red_triangle - 1.0f) * hsv.lane[1] + 1.0f) * hsv.lane[2],
        ((green_triangle - 1.0f) * hsv.lane[1] + 1.0f) * hsv.lane[2],
        ((blue_triangle - 1.0f) * hsv.lane[1] + 1.0f) * hsv.lane[2],
        hsv.lane[3],
    }};
    return result;
}

static int read_config(const char *path, float matrix[9], uint32_t white[2]) {
    uint8_t raw[52];
    FILE *input = fopen(path, "rb");
    if (input == NULL || fread(raw, 1, sizeof(raw), input) != sizeof(raw) ||
        fgetc(input) != EOF) {
        fprintf(stderr, "failed to read color config %s\n", path);
        if (input != NULL) {
            fclose(input);
        }
        return 0;
    }
    fclose(input);
    memcpy(matrix, raw, 9 * sizeof(float));
    memcpy(white, raw + 0x24, 2 * sizeof(uint32_t));
    return 1;
}

static void inverse_matrix(const float source[9], float inverse[9]) {
    float c00 = source[4] * source[8] - source[5] * source[7];
    float c01 = -(source[1] * source[8] - source[2] * source[7]);
    float c02 = source[1] * source[5] - source[2] * source[4];
    float c10 = -(source[3] * source[8] - source[5] * source[6]);
    float c11 = source[0] * source[8] - source[2] * source[6];
    float c12 = -(source[0] * source[5] - source[2] * source[3]);
    float c20 = source[3] * source[7] - source[4] * source[6];
    float c21 = -(source[0] * source[7] - source[1] * source[6]);
    float c22 = source[0] * source[4] - source[1] * source[3];
    float determinant =
        (source[0] * c00 + source[1] * c10) + source[2] * c20;
    float reciprocal = 1.0f / determinant;
    const float cofactors[9] = {
        c00, c01, c02, c10, c11, c12, c20, c21, c22,
    };
    for (int i = 0; i < 9; ++i) {
        inverse[i] = cofactors[i] * reciprocal;
    }
}

static void conversion_matrix(const float input[9],
                              const float destination[9], float output[9]) {
    float inverse[9];
    inverse_matrix(destination, inverse);
    for (int row = 0; row < 3; ++row) {
        for (int column = 0; column < 3; ++column) {
            float first = inverse[row * 3] * input[column];
            float second = inverse[row * 3 + 1] * input[3 + column];
            float third = inverse[row * 3 + 2] * input[6 + column];
            output[row * 3 + column] = (first + second) + third;
        }
    }
}

static Vec4 apply_conversion(Vec4 source, const float matrix[9]) {
    Vec4 result = source;
    for (int row = 0; row < 3; ++row) {
        float red = source.lane[0] * matrix[row * 3];
        float green = source.lane[1] * matrix[row * 3 + 1];
        float blue = source.lane[2] * matrix[row * 3 + 2];
        result.lane[row] = (blue + red) + green;
    }
    return result;
}

int main(int argc, char **argv) {
    if (argc < 4 || argc > 7) {
        fprintf(stderr,
                "usage: %s input.raw map.raw expected.raw [actual.raw]\n"
                "       %s input.raw map.raw expected.raw "
                "input.config output.config [actual.raw]\n",
                argv[0],
                argv[0]);
        return 2;
    }
    int full_conversion = argc >= 6;
    enum {
        kWidth = 652,
        kHeight = 489,
        kHueDivisions = 32,
        kSaturationDivisions = 32,
    };
    const size_t pixel_count = (size_t)kWidth * kHeight;
    const size_t image_size = pixel_count * sizeof(Vec4);
    const size_t map_count =
        (size_t)(kHueDivisions + 1) * (kSaturationDivisions + 1);
    const size_t map_size = map_count * sizeof(Vec4);
    Vec4 *input = read_file(argv[1], image_size);
    Vec4 *map = read_file(argv[2], map_size);
    Vec4 *expected = read_file(argv[3], image_size);
    Vec4 *actual = aligned_alloc(16, image_size);
    if (input == NULL || map == NULL || expected == NULL || actual == NULL) {
        return 1;
    }
    float matrix[9] = {0};
    if (full_conversion) {
        float input_config[9], output_config[9];
        uint32_t input_white[2], output_white[2];
        if (!read_config(argv[4], input_config, input_white) ||
            !read_config(argv[5], output_config, output_white) ||
            memcmp(input_white, output_white, sizeof(input_white)) != 0) {
            fprintf(stderr, "full replay requires equal-whitepoint color configs\n");
            return 1;
        }
        conversion_matrix(input_config, output_config, matrix);
    }
    for (size_t i = 0; i < pixel_count; ++i) {
        Vec4 converted = full_conversion ? apply_conversion(input[i], matrix) : input[i];
        actual[i] = hsv_to_rgb(apply_map(rgb_to_hsv(converted), map,
                                         kHueDivisions,
                                         kSaturationDivisions));
    }
    size_t different = 0;
    size_t first = image_size;
    const uint8_t *actual_bytes = (const uint8_t *)actual;
    const uint8_t *expected_bytes = (const uint8_t *)expected;
    for (size_t i = 0; i < image_size; ++i) {
        if (actual_bytes[i] != expected_bytes[i]) {
            if (first == image_size) {
                first = i;
            }
            ++different;
        }
    }
    printf("pixels=%zu map_vec4=%zu compared_bytes=%zu different_bytes=%zu",
           pixel_count, map_count, image_size, different);
    if (different != 0) {
        printf(" first_difference=%zu", first);
    }
    putchar('\n');
    printf("actual_first=%g,%g,%g,%g expected_first=%g,%g,%g,%g\n",
           actual[0].lane[0], actual[0].lane[1], actual[0].lane[2],
           actual[0].lane[3], expected[0].lane[0], expected[0].lane[1],
           expected[0].lane[2], expected[0].lane[3]);
    const char *output_path = argc == 5 ? argv[4] : (argc == 7 ? argv[6] : NULL);
    if (output_path != NULL) {
        FILE *output = fopen(output_path, "wb");
        if (output == NULL || fwrite(actual, 1, image_size, output) != image_size) {
            perror(output_path);
            if (output != NULL) {
                fclose(output);
            }
            return 1;
        }
        fclose(output);
    }
    free(actual);
    free(expected);
    free(map);
    free(input);
    return different == 0 ? 0 : 1;
}
