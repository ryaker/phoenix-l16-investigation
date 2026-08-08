#include <dlfcn.h>
#include <mach-o/dyld.h>
#include <mach/mach.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

#define LIBCP_PATH \
  "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
#define INVERSE_VA 0x1a2c10
#define SKIP_HELPERS_OFFSET 0x3c6
#define SKIP_STRIDE1_OFFSET 0x3d4
#define SKIP_STRIDE1_COLUMNS_OFFSET 0x594e
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

static int read_block(const char *path, float *block) {
  FILE *file = fopen(path, "rb");
  if (!file) return 0;
  size_t count = fread(block, sizeof(float), CELLS, file);
  fclose(file);
  return count == CELLS;
}

static int write_block(const char *path, const float *block) {
  FILE *file = fopen(path, "wb");
  if (!file) return 0;
  size_t count = fwrite(block, sizeof(float), CELLS, file);
  fclose(file);
  return count == CELLS;
}

int main(int argc, char **argv) {
  if (argc != 4 || (strcmp(argv[3], "coarse") && strcmp(argv[3], "stride2") &&
                    strcmp(argv[3], "stride1row"))) {
    fprintf(stderr, "usage: %s INPUT_F32 OUTPUT_F32 coarse|stride2|stride1row\n",
            argv[0]);
    return 2;
  }
  void *handle = dlopen(LIBCP_PATH, RTLD_NOW | RTLD_LOCAL);
  if (!handle) {
    fprintf(stderr, "dlopen failed: %s\n", dlerror());
    return 2;
  }
  intptr_t slide = libcp_slide();
  uint8_t *inverse = (uint8_t *)(slide + INVERSE_VA);
  const uint8_t expected_coarse[7] = {0xe8, 0x45, 0x53, 0x00, 0x00, 0x48, 0x89};
  const uint8_t expected_stride2[1] = {0xe9};
  const uint8_t expected_stride1row[7] = {0x48, 0xc7, 0xc0, 0xf0, 0xff, 0xff, 0xff};
  const uint8_t return_frame[7] = {0x48, 0x83, 0xc4, 0x08, 0x5b, 0x5d, 0xc3};
  const uint8_t return_direct[1] = {0xc3};
  uint8_t *patch;
  const uint8_t *expected;
  const uint8_t *replacement;
  size_t patch_size;
  if (!strcmp(argv[3], "coarse")) {
    patch = inverse + SKIP_HELPERS_OFFSET;
    expected = expected_coarse;
    replacement = return_frame;
    patch_size = 7;
  } else if (!strcmp(argv[3], "stride2")) {
    patch = inverse + SKIP_STRIDE1_OFFSET;
    expected = expected_stride2;
    replacement = return_direct;
    patch_size = 1;
  } else {
    patch = inverse + SKIP_STRIDE1_COLUMNS_OFFSET;
    expected = expected_stride1row;
    replacement = return_frame;
    patch_size = 7;
  }
  if (memcmp(patch, expected, patch_size) != 0) {
    fprintf(stderr, "installed inverse stage bytes changed\n");
    return 2;
  }

  float *block = NULL;
  if (posix_memalign((void **)&block, 16, CELLS * sizeof(float)) ||
      !read_block(argv[1], block)) {
    fprintf(stderr, "input read failed\n");
    return 2;
  }

  size_t page_size = (size_t)getpagesize();
  uintptr_t page = (uintptr_t)patch & ~(page_size - 1);
  if (mprotect((void *)page, page_size, PROT_READ | PROT_WRITE | PROT_EXEC)) {
    perror("mprotect");
    return 2;
  }
  uint8_t saved[7];
  memcpy(saved, patch, patch_size);
  memcpy(patch, replacement, patch_size);
  __builtin___clear_cache((char *)patch, (char *)patch + patch_size);

  ((transform_fn)inverse)(block);

  memcpy(patch, saved, patch_size);
  __builtin___clear_cache((char *)patch, (char *)patch + patch_size);
  mprotect((void *)page, page_size, PROT_READ | PROT_EXEC);

  int ok = write_block(argv[2], block);
  free(block);
  dlclose(handle);
  return ok ? 0 : 2;
}
