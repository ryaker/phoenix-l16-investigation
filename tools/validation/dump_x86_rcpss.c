// Exhaustive oracle for the unrefined x86 SSE reciprocal approximation.
// Build as x86_64 and run under Rosetta on Apple Silicon:
//   clang -arch x86_64 -O2 dump_x86_rcpss.c -o dump_x86_rcpss
//   arch -x86_64 ./dump_x86_rcpss table 127 out.u32le
//   arch -x86_64 ./dump_x86_rcpss bits 3f800000 3f000000

#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <xmmintrin.h>

static uint32_t rcp_bits(uint32_t bits) {
    float input;
    float output;
    memcpy(&input, &bits, sizeof(input));
    __m128 value = _mm_set_ss(input);
    value = _mm_rcp_ss(value);
    _mm_store_ss(&output, value);
    uint32_t result;
    memcpy(&result, &output, sizeof(result));
    return result;
}

static uint32_t rcpps_lane_bits(uint32_t bits) {
    float input;
    float output[4];
    memcpy(&input, &bits, sizeof(input));
    __m128 value = _mm_set_ps(3.0f, 2.0f, 1.0f, input);
    value = _mm_rcp_ps(value);
    _mm_storeu_ps(output, value);
    uint32_t result;
    memcpy(&result, &output[0], sizeof(result));
    return result;
}

// Portable bit formula observed for the installed Rosetta/x86 SSE oracle.
// Normal inputs use the top 11 fraction bits as a 2048-entry midpoint table.
// If i is that index, the normalized midpoint is (4097+2*i)/4096 and
// round((1/midpoint)*8192) is exactly the integer quotient below.
static uint32_t software_rcp_bits(uint32_t bits) {
    const uint32_t sign = bits & UINT32_C(0x80000000);
    const uint32_t exponent = (bits >> 23) & 0xff;
    const uint32_t fraction = bits & UINT32_C(0x007fffff);
    if (exponent == 0)
        return sign | UINT32_C(0x7f800000);  // zero/subnormal -> infinity
    if (exponent == 0xff) {
        if (fraction == 0)
            return sign;                    // infinity -> signed zero
        return bits | UINT32_C(0x00400000); // preserve payload, quiet NaN
    }
    if (exponent >= 253)
        return sign;                        // underflow flushes to signed zero

    const uint32_t index = fraction >> 12;
    const uint32_t denominator = 4097 + 2 * index;
    const uint32_t q = ((UINT32_C(1) << 25) + denominator / 2) / denominator;
    const uint32_t output_exponent = 253 - exponent;
    const uint32_t output_fraction = (q - 4096) << 11;
    return sign | (output_exponent << 23) | output_fraction;
}

static int selftest(void) {
    static const uint32_t lows[] = {0, 1, 0x555, 0xaaa, 0xffe, 0xfff};
    uint64_t count = 0;
    for (uint32_t sign = 0; sign <= UINT32_C(0x80000000);
         sign += UINT32_C(0x80000000)) {
        for (uint32_t exponent = 1; exponent <= 254; ++exponent) {
            for (uint32_t index = 0; index < 2048; ++index) {
                for (size_t j = 0; j < sizeof(lows) / sizeof(lows[0]); ++j) {
                    const uint32_t input = sign | (exponent << 23) |
                                           (index << 12) | lows[j];
                    const uint32_t expected = rcp_bits(input);
                    const uint32_t packed = rcpps_lane_bits(input);
                    const uint32_t actual = software_rcp_bits(input);
                    if (actual != expected || packed != expected) {
                        fprintf(stderr,
                                "mismatch input=%08" PRIx32 " software=%08" PRIx32
                                " rcpss=%08" PRIx32 " rcpps=%08" PRIx32 "\n",
                                input, actual, expected, packed);
                        return 1;
                    }
                    ++count;
                }
            }
        }
        if (sign != 0) break;
    }
    static const uint32_t specials[] = {
        0x00000000, 0x80000000, 0x00000001, 0x007fffff,
        0x80000001, 0x807fffff, 0x7f800000, 0xff800000,
        0x7f800001, 0x7fa00000, 0x7fbfffff, 0xff800001,
    };
    for (size_t i = 0; i < sizeof(specials) / sizeof(specials[0]); ++i) {
        const uint32_t input = specials[i];
        const uint32_t expected = rcp_bits(input);
        const uint32_t packed = rcpps_lane_bits(input);
        const uint32_t actual = software_rcp_bits(input);
        if (actual != expected || packed != expected) {
            fprintf(stderr,
                    "special mismatch input=%08" PRIx32 " software=%08" PRIx32
                    " rcpss=%08" PRIx32 " rcpps=%08" PRIx32 "\n",
                    input, actual, expected, packed);
            return 1;
        }
        ++count;
    }
    printf("rcpss_software_formula=OK cases=%" PRIu64 "\n", count);
    return 0;
}

static int dump_table(int exponent, const char *path) {
    if (exponent < 0 || exponent > 255) {
        fprintf(stderr, "exponent must be in 0..255\n");
        return 2;
    }
    FILE *output = fopen(path, "wb");
    if (!output) {
        fprintf(stderr, "cannot open %s: %s\n", path, strerror(errno));
        return 2;
    }
    enum { kChunk = 1 << 16 };
    uint32_t *buffer = malloc(kChunk * sizeof(*buffer));
    if (!buffer) {
        fclose(output);
        return 2;
    }
    for (uint32_t base = 0; base < (1u << 23); base += kChunk) {
        for (uint32_t i = 0; i < kChunk; ++i) {
            uint32_t input = ((uint32_t)exponent << 23) | (base + i);
            buffer[i] = rcp_bits(input);
        }
        if (fwrite(buffer, sizeof(*buffer), kChunk, output) != kChunk) {
            fprintf(stderr, "write failed: %s\n", strerror(errno));
            free(buffer);
            fclose(output);
            return 2;
        }
    }
    free(buffer);
    if (fclose(output) != 0) {
        fprintf(stderr, "close failed: %s\n", strerror(errno));
        return 2;
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc >= 2 && strcmp(argv[1], "table") == 0) {
        if (argc != 4) {
            fprintf(stderr, "usage: %s table EXPONENT OUT.u32le\n", argv[0]);
            return 2;
        }
        return dump_table((int)strtol(argv[2], NULL, 0), argv[3]);
    }
    if (argc >= 2 && strcmp(argv[1], "bits") == 0) {
        if (argc < 3) {
            fprintf(stderr, "usage: %s bits HEX [HEX ...]\n", argv[0]);
            return 2;
        }
        for (int i = 2; i < argc; ++i) {
            uint32_t input = (uint32_t)strtoul(argv[i], NULL, 16);
            printf("%08" PRIx32 " %08" PRIx32 "\n", input, rcp_bits(input));
        }
        return 0;
    }
    if (argc == 2 && strcmp(argv[1], "selftest") == 0)
        return selftest();
    fprintf(stderr, "usage: %s {table EXPONENT OUT|bits HEX...|selftest}\n", argv[0]);
    return 2;
}
