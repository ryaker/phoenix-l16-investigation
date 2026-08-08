#include <immintrin.h>
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

static __m128 fast_srgb_encode(__m128 linear) {
    const __m128 zero = _mm_setzero_ps();
    __m128 positive = _mm_max_ps(zero, linear);
    __m128 original = positive;

    __m128 mantissa = _mm_or_ps(
        _mm_and_ps(positive, _mm_castsi128_ps(_mm_set1_epi32(0x007fffff))),
        _mm_set1_ps(1.0f));
    __m128 log_poly = _mm_mul_ps(mantissa, _mm_set1_ps(f32_bits(0x3e511af3)));
    log_poly = _mm_add_ps(log_poly, _mm_set1_ps(f32_bits(0xbfa05375)));
    log_poly = _mm_mul_ps(log_poly, mantissa);

    __m128 exponent = _mm_castsi128_ps(_mm_srai_epi32(
        _mm_add_epi32(_mm_castps_si128(positive), _mm_set1_epi32(0xc0800000)),
        23));
    exponent = _mm_cvtepi32_ps(_mm_castps_si128(exponent));
    log_poly = _mm_add_ps(log_poly, _mm_set1_ps(f32_bits(0x40552f75)));
    log_poly = _mm_mul_ps(log_poly, mantissa);
    exponent = _mm_add_ps(exponent, _mm_set1_ps(f32_bits(0xc0121769)));
    exponent = _mm_add_ps(exponent, log_poly);
    exponent = _mm_mul_ps(exponent, _mm_set1_ps(f32_bits(0x3ed55555)));
    exponent = _mm_max_ps(exponent, _mm_set1_ps(-126.0f));
    exponent = _mm_min_ps(exponent, _mm_set1_ps(128.0f));

    __m128i truncated = _mm_cvttps_epi32(exponent);
    __m128i sign = _mm_srai_epi32(_mm_castps_si128(exponent), 31);
    __m128i floored = _mm_add_epi32(truncated, sign);
    __m128 fraction = _mm_sub_ps(exponent, _mm_cvtepi32_ps(floored));
    __m128 exp_poly = _mm_mul_ps(fraction, _mm_set1_ps(f32_bits(0x3d9fcb52)));
    exp_poly = _mm_add_ps(exp_poly, _mm_set1_ps(f32_bits(0x3e677e26)));
    exp_poly = _mm_mul_ps(exp_poly, fraction);
    exp_poly = _mm_add_ps(exp_poly, _mm_set1_ps(f32_bits(0x3f322226)));
    exp_poly = _mm_mul_ps(exp_poly, fraction);
    exp_poly = _mm_add_ps(exp_poly, _mm_set1_ps(f32_bits(0x3f7ffb19)));
    __m128 power = _mm_castsi128_ps(_mm_add_epi32(
        _mm_slli_epi32(floored, 23), _mm_castps_si128(exp_poly)));

    __m128 high = _mm_add_ps(
        _mm_mul_ps(power, _mm_set1_ps(f32_bits(0x3f870a3d))),
        _mm_set1_ps(f32_bits(0xbd6147ae)));
    __m128 low = _mm_mul_ps(original, _mm_set1_ps(f32_bits(0x414eb852)));
    __m128 low_mask = _mm_cmplt_ps(original, _mm_set1_ps(f32_bits(0x3b4d2e1c)));
    return _mm_blendv_ps(high, low, low_mask);
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
    if (argc != 3) {
        fprintf(stderr, "usage: %s INPUT_TILE_F32 OUTPUT_TILE_F32\n", argv[0]);
        return 2;
    }
    const size_t pixels = 256 * 256;
    const size_t size = pixels * 16;
    float *input = read_exact(argv[1], size);
    float *output = calloc(pixels * 4, sizeof(float));
    if (output == NULL) {
        return 1;
    }

    const __m128 row_r = _mm_castsi128_ps(_mm_setr_epi32(
        0x40022e50, 0xbe6a4e14, 0xbc0c6848, 0));
    const __m128 row_g = _mm_castsi128_ps(_mm_setr_epi32(
        0xbf3a3294, 0x3f9da957, 0xbe1cf72c, 0));
    const __m128 row_b = _mm_castsi128_ps(_mm_setr_epi32(
        0xbe9d0d46, 0xbb3f29b8, 0x3f94b7b9, 0));
    const __m128 alpha_row = _mm_castsi128_ps(_mm_setr_epi32(0, 0, 0, 0x3f800000));

    for (size_t i = 0; i < pixels; ++i) {
        __m128 source = _mm_loadu_ps(input + i * 4);
        __m128 transformed = _mm_mul_ps(
            _mm_shuffle_ps(source, source, _MM_SHUFFLE(0, 0, 0, 0)), row_r);
        __m128 green = _mm_mul_ps(
            _mm_shuffle_ps(source, source, _MM_SHUFFLE(1, 1, 1, 1)), row_g);
        __m128 blue = _mm_mul_ps(
            _mm_shuffle_ps(source, source, _MM_SHUFFLE(2, 2, 2, 2)), row_b);
        __m128 alpha = _mm_mul_ps(
            _mm_shuffle_ps(source, source, _MM_SHUFFLE(3, 3, 3, 3)), alpha_row);
        transformed = _mm_add_ps(alpha, blue);
        transformed = _mm_add_ps(transformed, _mm_mul_ps(
            _mm_shuffle_ps(source, source, _MM_SHUFFLE(0, 0, 0, 0)), row_r));
        transformed = _mm_add_ps(transformed, green);

        __m128 encoded = fast_srgb_encode(transformed);
        encoded = _mm_blend_ps(encoded, transformed, 0x8);
        _mm_storeu_ps(output + i * 4, encoded);
    }

    FILE *handle = fopen(argv[2], "wb");
    if (handle == NULL || fwrite(output, 1, size, handle) != size) {
        perror(argv[2]);
        return 1;
    }
    fclose(handle);
    printf("first_pixel=%.9g,%.9g,%.9g,%.9g\n",
           output[0], output[1], output[2], output[3]);
    free(output);
    free(input);
    return 0;
}
