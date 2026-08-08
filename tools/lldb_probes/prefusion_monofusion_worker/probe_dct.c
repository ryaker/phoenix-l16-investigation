#include <dlfcn.h>
#include <mach-o/dyld.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LIBCP_PATH \
  "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
#define FORWARD_VA 0x1a28f0
#define INVERSE_VA 0x1a2c10
#define SIDE 16
#define CELLS (SIDE * SIDE)

typedef void (*transform_fn)(float *);

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

static float max_abs_error(const float *a, const float *b) {
  float maximum = 0.0f;
  for (int index = 0; index < CELLS; ++index) {
    float error = fabsf(a[index] - b[index]);
    if (error > maximum) {
      maximum = error;
    }
  }
  return maximum;
}

static void print_matrix(const char *label, const float *values) {
  printf("%s", label);
  for (int index = 0; index < CELLS; ++index) {
    printf("%c%.9g", index ? ',' : '=', values[index]);
  }
  putchar('\n');
}

int main(void) {
  void *handle = dlopen(LIBCP_PATH, RTLD_NOW | RTLD_LOCAL);
  if (!handle) {
    fprintf(stderr, "dlopen failed: %s\n", dlerror());
    return 2;
  }

  intptr_t slide = libcp_slide();
  transform_fn forward = (transform_fn)(slide + FORWARD_VA);
  transform_fn inverse = (transform_fn)(slide + INVERSE_VA);
  float *block = NULL;
  float *original = NULL;
  if (posix_memalign((void **)&block, 16, CELLS * sizeof(float)) ||
      posix_memalign((void **)&original, 16, CELLS * sizeof(float))) {
    fprintf(stderr, "aligned allocation failed\n");
    return 2;
  }

  for (int index = 0; index < CELLS; ++index) {
    block[index] = 1.0f;
    original[index] = 1.0f;
  }
  forward(block);
  print_matrix("constant_forward", block);
  inverse(block);
  printf("constant_roundtrip_max_error=%.9g\n", max_abs_error(block, original));

  memset(block, 0, CELLS * sizeof(float));
  memset(original, 0, CELLS * sizeof(float));
  block[0] = 1.0f;
  original[0] = 1.0f;
  forward(block);
  print_matrix("impulse00_forward", block);
  inverse(block);
  printf("impulse00_roundtrip_max_error=%.9g\n", max_abs_error(block, original));

  memset(block, 0, CELLS * sizeof(float));
  memset(original, 0, CELLS * sizeof(float));
  block[1] = 1.0f;
  original[1] = 1.0f;
  forward(block);
  print_matrix("impulse01_forward", block);
  inverse(block);
  printf("impulse01_roundtrip_max_error=%.9g\n", max_abs_error(block, original));

  free(original);
  free(block);
  dlclose(handle);
  return 0;
}
