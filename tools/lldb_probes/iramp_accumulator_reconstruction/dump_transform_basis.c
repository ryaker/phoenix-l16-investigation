#include <dlfcn.h>
#include <mach-o/dyld.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LIBCP_PATH \
  "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
#define TRANSFORM_VA 0x36e5ef
#define SCRATCH_BYTES 0x2800
#define TILE_OFFSET 0x1580
#define SIDE 16
#define LANES 4

typedef float *(*transform_fn)(float *);

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

int main(int argc, char **argv) {
  if (argc != 2) {
    fprintf(stderr, "usage: %s BASIS.bin\n", argv[0]);
    return 2;
  }
  void *handle = dlopen(LIBCP_PATH, RTLD_NOW | RTLD_LOCAL);
  if (!handle) {
    fprintf(stderr, "dlopen failed: %s\n", dlerror());
    return 2;
  }
  transform_fn transform = (transform_fn)(libcp_slide() + TRANSFORM_VA);
  FILE *output = fopen(argv[1], "wb");
  if (!output) {
    perror(argv[1]);
    return 2;
  }

  unsigned char *scratch = NULL;
  if (posix_memalign((void **)&scratch, 16, SCRATCH_BYTES)) {
    fprintf(stderr, "aligned allocation failed\n");
    return 2;
  }
  for (int input = 0; input < SIDE * SIDE; ++input) {
    memset(scratch, 0, SCRATCH_BYTES);
    float *tile = (float *)(scratch + TILE_OFFSET);
    tile[input * LANES] = 1.0f;
    float *result = transform((float *)scratch);
    if ((unsigned char *)result != scratch + TILE_OFFSET) {
      fprintf(stderr, "unexpected return pointer for basis %d\n", input);
      return 2;
    }
    for (int output_index = 0; output_index < SIDE * SIDE; ++output_index) {
      if (fwrite(&tile[output_index * LANES], sizeof(float), 1, output) != 1) {
        fprintf(stderr, "basis output write failed\n");
        return 2;
      }
    }
  }

  fclose(output);
  free(scratch);
  dlclose(handle);
  printf("basis_responses=%d floats=%d\n", SIDE * SIDE,
         SIDE * SIDE * SIDE * SIDE);
  return 0;
}
