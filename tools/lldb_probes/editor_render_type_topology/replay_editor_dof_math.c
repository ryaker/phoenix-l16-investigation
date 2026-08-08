#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <xmmintrin.h>

static float from_bits(uint32_t bits) {
    float value;
    memcpy(&value, &bits, sizeof(value));
    return value;
}

static uint32_t to_bits(float value) {
    uint32_t bits;
    memcpy(&bits, &value, sizeof(bits));
    return bits;
}

static __m128 scalar(float value) {
    return _mm_set_ss(value);
}

static void focus_range(uint32_t input[5], uint32_t output[2]) {
    __m128 depth = scalar(from_bits(input[0]));
    __m128 focal = scalar(from_bits(input[1]));
    __m128 pitch = scalar(from_bits(input[2]));
    __m128 f_number = scalar(from_bits(input[3]));
    __m128 blur = scalar(from_bits(input[4]));
    __m128 one = scalar(1.0f);

    __m128 delta = _mm_sub_ss(depth, focal);
    __m128 hyper = _mm_div_ss(
        _mm_mul_ss(focal, focal),
        _mm_mul_ss(_mm_add_ss(pitch, pitch), f_number));
    __m128 q = _mm_mul_ss(_mm_div_ss(one, hyper),
                          _mm_mul_ss(delta, blur));
    __m128 near_depth = _mm_div_ss(depth, _mm_add_ss(one, q));
    __m128 far_depth = _mm_div_ss(depth, _mm_sub_ss(one, q));
    float far_value = _mm_cvtss_f32(far_depth);
    if (far_value < 0.0f) far_depth = scalar(100000.0f);
    far_depth = _mm_min_ss(far_depth, _mm_mul_ss(depth, scalar(10.0f)));

    output[0] = to_bits(_mm_cvtss_f32(near_depth));
    output[1] = to_bits(_mm_cvtss_f32(far_depth));
}

static __m128 endpoint_radius(__m128 depth, __m128 max_radius,
                              __m128 near_scale, __m128 hyper,
                              __m128 focus, __m128 focus_minus_focal) {
    __m128 selected = hyper;
    if (_mm_cvtss_f32(depth) < _mm_cvtss_f32(focus))
        selected = _mm_mul_ss(near_scale, hyper);
    __m128 reciprocal = _mm_rcp_ss(_mm_mul_ss(depth, focus_minus_focal));
    __m128 value = _mm_mul_ss(
        _mm_mul_ss(selected, _mm_sub_ss(depth, focus)), reciprocal);
    __m128 negative_cap = _mm_xor_ps(_mm_mul_ss(near_scale, max_radius),
                                     _mm_castsi128_ps(_mm_set1_epi32(0x80000000)));
    return _mm_min_ss(_mm_max_ss(value, negative_cap), max_radius);
}

static int tile_radius(uint32_t range[2], int depth_type, uint32_t input[4]) {
    int max_radius_i;
    float near_scale_f;
    if (depth_type == 0) {
        max_radius_i = 512;
        near_scale_f = 0.5f;
    } else if (depth_type == 1) {
        max_radius_i = 32;
        near_scale_f = 0.25f;
    } else {
        return -1;
    }

    __m128 focal = scalar(from_bits(input[0]));
    __m128 pitch = scalar(from_bits(input[1]));
    __m128 f_number = scalar(from_bits(input[2]));
    __m128 focus = scalar(from_bits(input[3]));
    __m128 focus_minus_focal = _mm_sub_ss(focus, focal);
    __m128 hyper = _mm_div_ss(
        _mm_mul_ss(focal, focal),
        _mm_mul_ss(_mm_add_ss(pitch, pitch), f_number));
    __m128 max_radius = scalar((float)max_radius_i);
    __m128 near_scale = scalar(near_scale_f);

    __m128 first = endpoint_radius(scalar(from_bits(range[0])), max_radius,
                                   near_scale, hyper, focus,
                                   focus_minus_focal);
    __m128 second = endpoint_radius(scalar(from_bits(range[1])), max_radius,
                                    near_scale, hyper, focus,
                                    focus_minus_focal);
    __m128 abs_mask = _mm_castsi128_ps(_mm_set1_epi32(0x7fffffff));
    float maximum = _mm_cvtss_f32(
        _mm_max_ss(_mm_and_ps(first, abs_mask),
                   _mm_and_ps(second, abs_mask)));
    int exponent = (int)(log2f(maximum) / log2(2.0)) + 1;
    return (int)(ldexp(1.0, exponent) * 1.600000023841858);
}

int main(void) {
    char kind;
    while (scanf(" %c", &kind) == 1) {
        if (kind == 'F') {
            uint32_t input[5], output[2];
            if (scanf(" %x %x %x %x %x", &input[0], &input[1], &input[2],
                      &input[3], &input[4]) != 5)
                return 2;
            focus_range(input, output);
            printf("F %08x %08x\n", output[0], output[1]);
        } else if (kind == 'R') {
            uint32_t range[2], input[4];
            int depth_type;
            if (scanf(" %x %x %d %x %x %x %x", &range[0], &range[1],
                      &depth_type, &input[0], &input[1], &input[2],
                      &input[3]) != 7)
                return 3;
            printf("R %d\n", tile_radius(range, depth_type, input));
        } else {
            return 4;
        }
    }
    return 0;
}
