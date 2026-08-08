#include <dlfcn.h>
#include <mach-o/dyld.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LIBCP_PATH \
  "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
#define SCORE_VA 0x36cde0
#define PATCH_BYTES 0x1000
#define SCRATCH_BYTES 0x2800
#define PATCH_FLOATS (PATCH_BYTES / sizeof(float))

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

static void read_exact(const char *path, void *buffer, size_t size) {
  FILE *input = fopen(path, "rb");
  if (!input) {
    perror(path);
    exit(2);
  }
  if (fread(buffer, 1, size, input) != size || fgetc(input) != EOF) {
    fprintf(stderr, "%s has unexpected size\n", path);
    exit(2);
  }
  fclose(input);
}

static float run_case(score_fn score, const unsigned char *scratch_source,
                      const float *candidate_source) {
  unsigned char *scratch = NULL;
  float *candidate = NULL;
  if (posix_memalign((void **)&scratch, 16, SCRATCH_BYTES) ||
      posix_memalign((void **)&candidate, 16, PATCH_BYTES)) {
    fprintf(stderr, "aligned allocation failed\n");
    exit(2);
  }
  memcpy(scratch, scratch_source, SCRATCH_BYTES);
  memcpy(candidate, candidate_source, PATCH_BYTES);
  float result = score((float *)scratch, candidate);
  free(scratch);
  free(candidate);
  return result;
}

static void print_case(score_fn score, const char *name,
                       const unsigned char *scratch, const float *candidate) {
  float result = run_case(score, scratch, candidate);
  uint32_t bits;
  memcpy(&bits, &result, sizeof(bits));
  printf("%s=%.9g bits=0x%08x\n", name, result, bits);
}

int main(int argc, char **argv) {
  if (argc != 3) {
    fprintf(stderr, "usage: %s SCRATCH.bin CANDIDATE.bin\n", argv[0]);
    return 2;
  }
  void *handle = dlopen(LIBCP_PATH, RTLD_NOW | RTLD_LOCAL);
  if (!handle) {
    fprintf(stderr, "dlopen failed: %s\n", dlerror());
    return 2;
  }
  score_fn score = (score_fn)(libcp_slide() + SCORE_VA);

  unsigned char *scratch = NULL;
  float *candidate = NULL;
  float *work = NULL;
  if (posix_memalign((void **)&scratch, 16, SCRATCH_BYTES) ||
      posix_memalign((void **)&candidate, 16, PATCH_BYTES) ||
      posix_memalign((void **)&work, 16, PATCH_BYTES)) {
    fprintf(stderr, "aligned allocation failed\n");
    return 2;
  }
  read_exact(argv[1], scratch, SCRATCH_BYTES);
  read_exact(argv[2], candidate, PATCH_BYTES);

  print_case(score, "captured", scratch, candidate);

  memcpy(work, scratch, PATCH_BYTES);
  print_case(score, "reference_identical", scratch, work);

  memset(work, 0, PATCH_BYTES);
  print_case(score, "candidate_zero", scratch, work);

  memcpy(work, candidate, PATCH_BYTES);
  for (size_t index = 0; index < PATCH_FLOATS; ++index) {
    work[index] = work[index] * 1.1f + 0.03f;
  }
  print_case(score, "candidate_affine", scratch, work);

  memcpy(work, candidate, PATCH_BYTES);
  work[0] += 0.25f;
  print_case(score, "candidate_one_sample_delta", scratch, work);

  for (int lane = 0; lane < 4; ++lane) {
    memcpy(work, candidate, PATCH_BYTES);
    for (size_t index = lane; index < PATCH_FLOATS; index += 4) {
      work[index] = -work[index];
    }
    char name[64];
    snprintf(name, sizeof(name), "candidate_lane%d_sign_flip", lane);
    print_case(score, name, scratch, work);
  }

  for (int lane = 0; lane < 4; ++lane) {
    memcpy(work, candidate, PATCH_BYTES);
    for (size_t index = lane; index < PATCH_FLOATS; index += 4) {
      work[index] = 0.0f;
    }
    char name[64];
    snprintf(name, sizeof(name), "candidate_lane%d_zero", lane);
    print_case(score, name, scratch, work);
  }

  memcpy(work, candidate, PATCH_BYTES);
  work[(8 * 16 + 8) * 4] += 0.25f;
  print_case(score, "candidate_center_lane0_delta", scratch, work);

  free(scratch);
  free(candidate);
  free(work);
  dlclose(handle);
  return 0;
}
