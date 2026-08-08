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
#define CELLS 256

typedef void (*transform_fn)(float *);

static intptr_t libcp_slide(void) {
  for (uint32_t index = 0; index < _dyld_image_count(); ++index) {
    const char *name = _dyld_get_image_name(index);
    if (name && strstr(name, "libcp.dylib")) {
      return _dyld_get_image_vmaddr_slide(index);
    }
  }
  return 0;
}

int main(int argc, char **argv) {
  if (argc != 4 || (strcmp(argv[3], "forward") && strcmp(argv[3], "inverse"))) {
    fprintf(stderr, "usage: %s INPUT_F32 OUTPUT_F32 forward|inverse\n", argv[0]);
    return 2;
  }
  void *handle = dlopen(LIBCP_PATH, RTLD_NOW | RTLD_LOCAL);
  if (!handle) {
    fprintf(stderr, "dlopen failed: %s\n", dlerror());
    return 2;
  }
  intptr_t slide = libcp_slide();
  transform_fn transform = (transform_fn)(
      slide + (!strcmp(argv[3], "forward") ? FORWARD_VA : INVERSE_VA));
  FILE *input = fopen(argv[1], "rb");
  FILE *output = fopen(argv[2], "wb");
  if (!input || !output) {
    perror("fopen");
    return 2;
  }
  float *block = NULL;
  if (posix_memalign((void **)&block, 16, CELLS * sizeof(float))) {
    fprintf(stderr, "aligned allocation failed\n");
    return 2;
  }
  size_t blocks = 0;
  for (;;) {
    size_t count = fread(block, sizeof(float), CELLS, input);
    if (count == 0 && feof(input)) break;
    if (count != CELLS) {
      fprintf(stderr, "partial input block\n");
      return 2;
    }
    transform(block);
    if (fwrite(block, sizeof(float), CELLS, output) != CELLS) {
      fprintf(stderr, "short output write\n");
      return 2;
    }
    ++blocks;
  }
  fprintf(stderr, "transform_batch=%s blocks=%zu\n", argv[3], blocks);
  free(block);
  fclose(input);
  fclose(output);
  dlclose(handle);
  return 0;
}
