#include <immintrin.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static float f32_bits(uint32_t bits) {
    union {
        uint32_t u;
        float f;
    } value = {bits};
    return value.f;
}

static float lut_sample(float shaped, const float *lut) {
    __m128 position = _mm_mul_ss(_mm_set_ss(shaped), _mm_set_ss(1024.0f));
    int index = _mm_cvttss_si32(position);
    if (index < 0) {
        index = 0;
    } else if (index > 1023) {
        index = 1023;
    }
    __m128 lower = _mm_load_ss(lut + index);
    __m128 delta = _mm_sub_ss(_mm_load_ss(lut + index + 1), lower);
    __m128 fraction = _mm_sub_ss(position, _mm_cvtsi32_ss(_mm_setzero_ps(), index));
    return _mm_cvtss_f32(_mm_add_ss(_mm_mul_ss(fraction, delta), lower));
}

static float reconstructed_midpoint(float low_x, float mid_x, float high_x,
                                    float low_y, float high_y) {
    __m128 numerator = _mm_mul_ss(
        _mm_sub_ss(_mm_set_ss(mid_x), _mm_set_ss(low_x)),
        _mm_sub_ss(_mm_set_ss(high_y), _mm_set_ss(low_y)));
    __m128 reciprocal = _mm_rcp_ss(
        _mm_sub_ss(_mm_set_ss(high_x), _mm_set_ss(low_x)));
    return _mm_cvtss_f32(
        _mm_add_ss(_mm_mul_ss(numerator, reciprocal), _mm_set_ss(low_y)));
}

static void replay_pixel(float destination[4], const float source[4],
                         float exposure_scale, const float *lut) {
    __m128 input = _mm_loadu_ps(source);
    __m128 scaled = _mm_mul_ps(input, _mm_set1_ps(exposure_scale));

    __m128 toe = _mm_add_ps(scaled, _mm_set1_ps(f32_bits(0xbb23d70b)));
    toe = _mm_mul_ps(toe, toe);
    toe = _mm_mul_ps(toe, _mm_set1_ps(f32_bits(0x42c90149)));
    __m128 toe_mask = _mm_cmple_ps(scaled, _mm_set1_ps(f32_bits(0x3b23d70b)));
    toe = _mm_blendv_ps(toe, _mm_setzero_ps(), toe_mask);

    __m128 linear = _mm_add_ps(scaled, _mm_set1_ps(f32_bits(0xbba3d70b)));
    linear = _mm_mul_ps(linear, _mm_set1_ps(f32_bits(0x3f80a4aa)));
    __m128 linear_mask = _mm_cmple_ps(
        _mm_set1_ps(f32_bits(0x3bf5c290)), scaled);
    __m128 shaped = _mm_blendv_ps(toe, linear, linear_mask);

    float x[4];
    _mm_storeu_ps(x, shaped);
    float y[3] = {
        lut_sample(x[0], lut),
        lut_sample(x[1], lut),
        lut_sample(x[2], lut),
    };

    int order[3] = {0, 1, 2};
    for (int i = 1; i < 3; ++i) {
        int current = order[i];
        int j = i;
        while (j > 0 && x[current] < x[order[j - 1]]) {
            order[j] = order[j - 1];
            --j;
        }
        order[j] = current;
    }

    destination[order[0]] = y[order[0]];
    destination[order[2]] = y[order[2]];
    if (x[order[0]] == x[order[2]]) {
        destination[order[1]] = y[order[1]];
    } else {
        destination[order[1]] = reconstructed_midpoint(
            x[order[0]], x[order[1]], x[order[2]],
            y[order[0]], y[order[2]]);
    }
    destination[3] = source[3];
}

static void *read_exact(const char *path, size_t size) {
    FILE *handle = fopen(path, "rb");
    if (handle == NULL) {
        perror(path);
        exit(1);
    }
    void *data = malloc(size);
    if (data == NULL || fread(data, 1, size, handle) != size || fgetc(handle) != EOF) {
        fprintf(stderr, "unexpected file size: %s\n", path);
        exit(1);
    }
    fclose(handle);
    return data;
}

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "usage: %s INPUT_RGBA_F32 LUT_1025_F32 OUTPUT_TILE_F32\n", argv[0]);
        return 2;
    }
    const int width = 652;
    const int height = 489;
    const int tile = 256;
    size_t input_size = (size_t)width * height * 4 * sizeof(float);
    float *input = read_exact(argv[1], input_size);
    float *lut = read_exact(argv[2], 1025 * sizeof(float));
    float *output = calloc((size_t)tile * tile * 4, sizeof(float));
    if (output == NULL) {
        return 1;
    }

    float exposure_scale = exp2f(f32_bits(0x3f80037e));
    for (int y = 0; y < tile; ++y) {
        for (int x = 0; x < tile; ++x) {
            replay_pixel(output + ((size_t)y * tile + x) * 4,
                         input + ((size_t)y * width + x) * 4,
                         exposure_scale, lut);
        }
    }

    FILE *handle = fopen(argv[3], "wb");
    if (handle == NULL || fwrite(output, 1, (size_t)tile * tile * 16, handle)
            != (size_t)tile * tile * 16) {
        perror(argv[3]);
        return 1;
    }
    fclose(handle);
    printf("exposure_scale=%.9g\n", exposure_scale);
    printf("first_pixel=%.9g,%.9g,%.9g,%.9g\n",
           output[0], output[1], output[2], output[3]);
    free(output);
    free(lut);
    free(input);
    return 0;
}
