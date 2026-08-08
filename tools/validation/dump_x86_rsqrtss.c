// Exhaustive oracle and derivation for the unrefined x86 SSE reciprocal-square-root
// approximation (RSQRTSS / RSQRTPS).
//
// Sibling of dump_x86_rcpss.c.  Build and run on any x86_64 host (on an Apple
// Silicon Mac, build with -arch x86_64 and run under Rosetta):
//   cc -O2 dump_x86_rsqrtss.c -o dump_x86_rsqrtss -lm
//   ./dump_x86_rsqrtss selftest      # all 2^32 inputs vs the software formula
//   ./dump_x86_rsqrtss structure     # re-derives the table geometry from scratch
//   ./dump_x86_rsqrtss bits 3f800000 40000000
//   ./dump_x86_rsqrtss table 127 out.u32le
//
// WHAT THE STRUCTURE PASS PROVES
//   For every one of the 254 finite exponents, across all 2^23 fractions, the
//   result changes only at fractions that are multiples of 0x2000.  The seed is
//   therefore a 1024-entry table indexed by (fraction >> 13), selected by the
//   exponent's parity -- 2048 entries total, the same table size the RCPSS seed
//   uses (which instead indexes fraction >> 12 with no parity split, because
//   reciprocal does not care about the exponent's parity and reciprocal-sqrt does).
//
// THE VALUE FORMULA
//   Let j = fraction >> 13 and d = 2049 + 2j, so the bin's midpoint mantissa is
//   d/2048 in [1, 2).  Let p = 1 - (exponent & 1), i.e. p = 0 when the binary
//   exponent (exponent - 127) is even and p = 1 when it is odd; in the odd case the
//   odd power of two is folded into the radicand, doubling it.  Then
//       Q = round( sqrt( 2^(37-p) / d ) )   in [4096, 8192]
//   and the result is  Q * 2^(-13-s)  with s = (exponent - 127 - p)/2, encoded as
//       exponent field = 126 - s,   fraction field = (Q - 4096) << 11.
//   d is odd and greater than one, so 2^(39-p)/d is never an exact (2Q+1)^2 and the
//   rounding has no ties to break -- the formula is unambiguous.
//
// SPECIALS (all confirmed by the exhaustive selftest)
//   +0/+subnormal -> +inf;  -0/-subnormal -> -inf;  +inf -> +0;  -inf -> 0xffc00000;
//   any negative normal -> 0xffc00000 (real indefinite);  NaN -> bits | 0x00400000.

#include <errno.h>
#include <inttypes.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <xmmintrin.h>

static uint32_t rsqrt_bits(uint32_t bits) {
    float input, output;
    memcpy(&input, &bits, sizeof(input));
    __m128 value = _mm_set_ss(input);
    value = _mm_rsqrt_ss(value);
    _mm_store_ss(&output, value);
    uint32_t result;
    memcpy(&result, &output, sizeof(result));
    return result;
}

static uint32_t rsqrtps_lane_bits(uint32_t bits) {
    float input;
    float output[4];
    memcpy(&input, &bits, sizeof(input));
    __m128 value = _mm_set_ps(3.0f, 2.0f, 1.0f, input);
    value = _mm_rsqrt_ps(value);
    _mm_storeu_ps(output, value);
    uint32_t result;
    memcpy(&result, &output[0], sizeof(result));
    return result;
}

// Smallest Q in [4096, 8192] with (2Q+1)^2 * d > 2^(39-p).  Pure integer, no libm.
// This is exactly the C++ shipped in phoenix/engine/common/x86_rsqrt.h.
static uint32_t seed_q(uint32_t bin, uint32_t parity) {
    const uint64_t d = 2049u + 2u * bin;
    const uint64_t m = (uint64_t)1 << (39u - parity);
    uint32_t lo = 4096u, hi = 8192u;
    while (lo < hi) {
        const uint32_t mid = lo + (hi - lo) / 2u;
        const uint64_t t = (uint64_t)2 * mid + 1u;
        if (t * t * d > m) hi = mid; else lo = mid + 1u;
    }
    return lo;
}

static uint32_t software_rsqrt_bits(uint32_t bits) {
    const uint32_t sign = bits & UINT32_C(0x80000000);
    const uint32_t exponent = (bits >> 23) & 0xff;
    const uint32_t fraction = bits & UINT32_C(0x007fffff);

    if (exponent == 0xff) {
        if (fraction) return bits | UINT32_C(0x00400000);  // NaN -> quieted
        if (!sign)    return UINT32_C(0x00000000);         // +inf -> +0
        return UINT32_C(0xffc00000);                       // -inf -> real indefinite
    }
    if (sign) {
        if (exponent == 0) return UINT32_C(0xff800000);    // -0 / -subnormal -> -inf
        return UINT32_C(0xffc00000);                       // negative -> real indefinite
    }
    if (exponent == 0) return UINT32_C(0x7f800000);        // +0 / +subnormal -> +inf

    const uint32_t parity = 1u - (exponent & 1u);
    const int scale = ((int)exponent - 127 - (int)parity) / 2;
    const uint32_t q = seed_q(fraction >> 13, parity);
    const uint32_t output_exponent = (uint32_t)(126 - scale) & 0xff;
    return (output_exponent << 23) | ((q - 4096u) << 11);
}

// Re-derive the table geometry with no assumptions: for each finite exponent, OR
// together every fraction at which the result changes.  The lowest set bit of that
// OR is the bin width.  Also checks that the mantissa depends only on the
// exponent's parity, and that RSQRTSS and RSQRTPS lane 0 agree.
static int structure(void) {
    int width_bit_min = 99, width_bit_max = -1;
    for (uint32_t e = 1; e <= 254; ++e) {
        uint32_t prev = rsqrt_bits(e << 23), changed = 0;
        for (uint32_t f = 1; f < (1u << 23); ++f) {
            const uint32_t cur = rsqrt_bits((e << 23) | f);
            if (cur != prev) { changed |= f; prev = cur; }
        }
        int k = 0;
        while (k < 23 && !((changed >> k) & 1)) ++k;
        if (k < width_bit_min) width_bit_min = k;
        if (k > width_bit_max) width_bit_max = k;
    }
    printf("bin_width_bit min=%d max=%d (expect 13,13 -> 1024 bins)\n",
           width_bit_min, width_bit_max);

    int parity_only = 1;
    for (uint32_t e = 1; e + 2 <= 254 && parity_only; ++e)
        for (uint32_t j = 0; j < 1024; ++j)
            if ((rsqrt_bits((e << 23) | (j << 13)) & 0x007fffff) !=
                (rsqrt_bits(((e + 2) << 23) | (j << 13)) & 0x007fffff)) {
                printf("parity break e=%u j=%u\n", e, j); parity_only = 0; break;
            }
    printf("mantissa_depends_only_on_exponent_parity=%d\n", parity_only);

    uint32_t or_frac = 0;
    for (uint32_t e = 1; e <= 254; ++e)
        for (uint32_t j = 0; j < 1024; ++j)
            or_frac |= rsqrt_bits((e << 23) | (j << 13)) & 0x007fffff;
    int lowzero = 0;
    while (lowzero < 23 && !((or_frac >> lowzero) & 1)) ++lowzero;
    printf("output_fraction_OR=%06" PRIx32 " low_always_zero_bits=%d (expect 11)\n",
           or_frac, lowzero);
    return (width_bit_min == 13 && width_bit_max == 13 && parity_only && lowzero == 11)
               ? 0 : 1;
}

static int selftest(void) {
    uint64_t bad = 0, badps = 0;
    for (uint64_t b = 0; b < (UINT64_C(1) << 32); ++b) {
        const uint32_t bits = (uint32_t)b;
        const uint32_t expected = rsqrt_bits(bits);
        const uint32_t actual = software_rsqrt_bits(bits);
        if (actual != expected) {
            if (bad < 8)
                fprintf(stderr, "mismatch input=%08" PRIx32 " rsqrtss=%08" PRIx32
                                " software=%08" PRIx32 "\n", bits, expected, actual);
            ++bad;
        }
    }
    for (uint64_t b = 0; b < (UINT64_C(1) << 32); b += 1021) {
        const uint32_t bits = (uint32_t)b;
        const uint32_t packed = rsqrtps_lane_bits(bits);
        if (packed != software_rsqrt_bits(bits)) {
            if (badps < 8)
                fprintf(stderr, "packed mismatch input=%08" PRIx32 " rsqrtps=%08" PRIx32
                                " software=%08" PRIx32 "\n", bits, packed,
                        software_rsqrt_bits(bits));
            ++badps;
        }
    }
    printf("rsqrtss_software_formula=%s cases=4294967296 mismatches=%" PRIu64 "\n",
           bad ? "FAIL" : "OK", bad);
    printf("rsqrtps_lane0_stride1021=%s mismatches=%" PRIu64 "\n",
           badps ? "FAIL" : "OK", badps);
    return (bad || badps) ? 1 : 0;
}

static int dump_table(int exponent, const char *path) {
    if (exponent < 0 || exponent > 255) {
        fprintf(stderr, "exponent must be in 0..255\n");
        return 2;
    }
    FILE *output = fopen(path, "wb");
    if (!output) { fprintf(stderr, "cannot open %s: %s\n", path, strerror(errno)); return 2; }
    enum { kChunk = 1 << 16 };
    uint32_t *buffer = malloc(kChunk * sizeof(*buffer));
    if (!buffer) { fclose(output); return 2; }
    for (uint32_t base = 0; base < (1u << 23); base += kChunk) {
        for (uint32_t i = 0; i < kChunk; ++i)
            buffer[i] = rsqrt_bits(((uint32_t)exponent << 23) | (base + i));
        if (fwrite(buffer, sizeof(*buffer), kChunk, output) != kChunk) {
            fprintf(stderr, "write failed: %s\n", strerror(errno));
            free(buffer); fclose(output); return 2;
        }
    }
    free(buffer);
    if (fclose(output) != 0) { fprintf(stderr, "close failed: %s\n", strerror(errno)); return 2; }
    return 0;
}

int main(int argc, char **argv) {
    if (argc >= 2 && strcmp(argv[1], "table") == 0) {
        if (argc != 4) { fprintf(stderr, "usage: %s table EXPONENT OUT.u32le\n", argv[0]); return 2; }
        return dump_table((int)strtol(argv[2], NULL, 0), argv[3]);
    }
    if (argc >= 3 && strcmp(argv[1], "bits") == 0) {
        for (int i = 2; i < argc; ++i) {
            const uint32_t input = (uint32_t)strtoul(argv[i], NULL, 16);
            printf("%08" PRIx32 " %08" PRIx32 " %08" PRIx32 "\n",
                   input, rsqrt_bits(input), software_rsqrt_bits(input));
        }
        return 0;
    }
    if (argc == 2 && strcmp(argv[1], "structure") == 0) return structure();
    if (argc == 2 && strcmp(argv[1], "selftest") == 0) return selftest();
    fprintf(stderr, "usage: %s {selftest|structure|bits HEX...|table EXPONENT OUT}\n", argv[0]);
    return 2;
}
