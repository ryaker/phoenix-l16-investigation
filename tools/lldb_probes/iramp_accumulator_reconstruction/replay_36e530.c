#include <dlfcn.h>
#include <mach-o/dyld.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LIBCP_PATH \
  "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
#define PREP_VA 0x36e530
#define SCRATCH_BYTES 0x2800

typedef float *(*prep_fn)(float *);

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

int main(int argc, char **argv) {
  if (argc != 3) {
    fprintf(stderr, "usage: %s BEFORE.bin EXPECTED_AFTER.bin\n", argv[0]);
    return 2;
  }
  void *handle = dlopen(LIBCP_PATH, RTLD_NOW | RTLD_LOCAL);
  if (!handle) {
    fprintf(stderr, "dlopen failed: %s\n", dlerror());
    return 2;
  }
  prep_fn prep = (prep_fn)(libcp_slide() + PREP_VA);

  unsigned char *scratch = NULL;
  unsigned char *expected = NULL;
  if (posix_memalign((void **)&scratch, 16, SCRATCH_BYTES) ||
      posix_memalign((void **)&expected, 16, SCRATCH_BYTES)) {
    fprintf(stderr, "aligned allocation failed\n");
    return 2;
  }
  read_exact(argv[1], scratch, SCRATCH_BYTES);
  read_exact(argv[2], expected, SCRATCH_BYTES);

  float *result = prep((float *)scratch);
  size_t mismatches = 0;
  size_t first = SCRATCH_BYTES;
  for (size_t index = 0; index < SCRATCH_BYTES; ++index) {
    if (scratch[index] != expected[index]) {
      if (first == SCRATCH_BYTES) {
        first = index;
      }
      ++mismatches;
    }
  }
  float first_vec4[4];
  memcpy(first_vec4, scratch + 0x1580, sizeof(first_vec4));
  printf("return_offset=0x%tx mismatched_bytes=%zu",
         (unsigned char *)result - scratch, mismatches);
  if (mismatches) {
    printf(" first_mismatch=0x%zx", first);
  }
  printf("\noutput_first_vec4=%.9g,%.9g,%.9g,%.9g\n", first_vec4[0],
         first_vec4[1], first_vec4[2], first_vec4[3]);

  free(scratch);
  free(expected);
  dlclose(handle);
  return mismatches ? 1 : 0;
}
