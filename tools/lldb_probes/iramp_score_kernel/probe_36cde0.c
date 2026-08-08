#include <dlfcn.h>
#include <mach-o/dyld.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LIBCP_PATH \
  "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
#define SCORE_VA 0x36cde0
#define SIDE 16
#define LANES 4
#define PATCH_FLOATS (SIDE * SIDE * LANES)
#define SCRATCH_BYTES 0x3000

typedef float (*score_fn)(float *, float *);

static intptr_t libcp_slide(void) {
  uint32_t count = _dyld_image_count();
  for (uint32_t index = 0; index < count; ++index) {
    const char *name = _dyld_get_image_name(index);
    if (name && strstr(name, "libcp.dylib")) {
      return _dyld_get_image_vmaddr_slide(index);
    }
  }
  fprintf(stderr, "libcp image was not loaded\n");
  exit(2);
}

static uint32_t next_random(uint32_t *state) {
  *state = *state * 1664525u + 1013904223u;
  return *state;
}

static void fill_random(float *patch, uint32_t seed) {
  for (int index = 0; index < PATCH_FLOATS; ++index) {
    uint32_t value = next_random(&seed);
    patch[index] = ((float)(value >> 8) / 16777216.0f) * 2.0f - 1.0f;
  }
}

static float run_case(score_fn score, const float *reference,
                      const float *candidate) {
  float *scratch = NULL;
  float *work = NULL;
  if (posix_memalign((void **)&scratch, 16, SCRATCH_BYTES) ||
      posix_memalign((void **)&work, 16, PATCH_FLOATS * sizeof(float))) {
    fprintf(stderr, "aligned allocation failed\n");
    exit(2);
  }
  memset(scratch, 0, SCRATCH_BYTES);
  memcpy(scratch, reference, PATCH_FLOATS * sizeof(float));
  memcpy(work, candidate, PATCH_FLOATS * sizeof(float));
  float result = score(scratch, work);
  free(scratch);
  free(work);
  return result;
}

static void print_case(score_fn score, const char *name,
                       const float *reference, const float *candidate) {
  float result = run_case(score, reference, candidate);
  printf("%s=%.9g bits=0x%08x\n", name, result,
         *(const uint32_t *)&result);
}

int main(void) {
  void *handle = dlopen(LIBCP_PATH, RTLD_NOW | RTLD_LOCAL);
  if (!handle) {
    fprintf(stderr, "dlopen failed: %s\n", dlerror());
    return 2;
  }
  score_fn score = (score_fn)(libcp_slide() + SCORE_VA);

  float *reference = NULL;
  float *candidate = NULL;
  if (posix_memalign((void **)&reference, 16, PATCH_FLOATS * sizeof(float)) ||
      posix_memalign((void **)&candidate, 16, PATCH_FLOATS * sizeof(float))) {
    fprintf(stderr, "aligned allocation failed\n");
    return 2;
  }

  memset(reference, 0, PATCH_FLOATS * sizeof(float));
  memset(candidate, 0, PATCH_FLOATS * sizeof(float));
  print_case(score, "zero_zero", reference, candidate);

  for (int index = 0; index < PATCH_FLOATS; ++index) {
    reference[index] = 0.25f;
    candidate[index] = 0.25f;
  }
  print_case(score, "constant_identical", reference, candidate);

  fill_random(reference, 0x12345678u);
  memcpy(candidate, reference, PATCH_FLOATS * sizeof(float));
  print_case(score, "random_identical", reference, candidate);

  fill_random(candidate, 0x87654321u);
  print_case(score, "random_independent", reference, candidate);

  for (int index = 0; index < PATCH_FLOATS; ++index) {
    candidate[index] = reference[index] * 1.1f + 0.03f;
  }
  print_case(score, "random_affine", reference, candidate);

  memcpy(candidate, reference, PATCH_FLOATS * sizeof(float));
  candidate[0] += 0.25f;
  print_case(score, "one_sample_delta", reference, candidate);

  for (int index = 0; index < PATCH_FLOATS; index += LANES) {
    candidate[index + 0] = reference[index + 0];
    candidate[index + 1] = -reference[index + 1];
    candidate[index + 2] = reference[index + 2];
    candidate[index + 3] = reference[index + 3];
  }
  print_case(score, "lane1_sign_flip", reference, candidate);

  free(reference);
  free(candidate);
  dlclose(handle);
  return 0;
}
