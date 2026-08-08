#include <dlfcn.h>
#include <mach-o/dyld.h>
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

int main(int argc, char **argv) {
  if (argc != 3) {
    fprintf(stderr, "usage: %s FORWARD.bin INVERSE.bin\n", argv[0]);
    return 2;
  }
  void *handle = dlopen(LIBCP_PATH, RTLD_NOW | RTLD_LOCAL);
  if (!handle) {
    fprintf(stderr, "dlopen failed: %s\n", dlerror());
    return 2;
  }
  transform_fn forward = (transform_fn)(libcp_slide() + FORWARD_VA);
  transform_fn inverse = (transform_fn)(libcp_slide() + INVERSE_VA);
  FILE *forward_output = fopen(argv[1], "wb");
  FILE *inverse_output = fopen(argv[2], "wb");
  if (!forward_output || !inverse_output) {
    perror("fopen output");
    return 2;
  }
  float *block = NULL;
  if (posix_memalign((void **)&block, 16, CELLS * sizeof(float))) {
    fprintf(stderr, "aligned allocation failed\n");
    return 2;
  }
  for (int basis = 0; basis < CELLS; ++basis) {
    memset(block, 0, CELLS * sizeof(float));
    block[basis] = 1.0f;
    forward(block);
    if (fwrite(block, sizeof(float), CELLS, forward_output) != CELLS) {
      fprintf(stderr, "short forward write\n");
      return 2;
    }
    memset(block, 0, CELLS * sizeof(float));
    block[basis] = 1.0f;
    inverse(block);
    if (fwrite(block, sizeof(float), CELLS, inverse_output) != CELLS) {
      fprintf(stderr, "short inverse write\n");
      return 2;
    }
  }
  free(block);
  fclose(forward_output);
  fclose(inverse_output);
  dlclose(handle);
  return 0;
}
