#include <dlfcn.h>
#include <inttypes.h>
#include <mach-o/dyld.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *kLibcp =
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib";

static uintptr_t find_libcp_base(void) {
    for (uint32_t i = 0; i < _dyld_image_count(); ++i) {
        const char *name = _dyld_get_image_name(i);
        if (name != NULL && strstr(name, "/libcp.dylib") != NULL) {
            return (uintptr_t)_dyld_get_image_header(i);
        }
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s x y\n", argv[0]);
        return 2;
    }
    void *handle = dlopen(kLibcp, RTLD_NOW | RTLD_LOCAL);
    uintptr_t base = find_libcp_base();
    if (handle == NULL || base == 0) {
        fprintf(stderr, "failed to load libcp: %s\n", dlerror());
        return 1;
    }
    float xy[2] = {(float)strtod(argv[1], NULL), (float)strtod(argv[2], NULL)};
    float result[2] = {0.0f, 0.0f};
    typedef void (*cct_fn)(float *, const float *);
    ((cct_fn)(base + 0xab2e0))(result, xy);
    typedef const void *(*converter_select_fn)(int, int);
    const void *converter = ((converter_select_fn)(base + 0xaa110))(0, 5);
    uint32_t x_word, y_word, cct_word, auxiliary_word;
    memcpy(&x_word, xy, sizeof(x_word));
    memcpy(&y_word, xy + 1, sizeof(y_word));
    memcpy(&cct_word, result, sizeof(cct_word));
    memcpy(&auxiliary_word, result + 1, sizeof(auxiliary_word));
    printf(
        "{\n"
        "  \"xy\": [%.17g, %.17g],\n"
        "  \"xy_words\": [\"0x%08x\", \"0x%08x\"],\n"
        "  \"cct\": %.17g,\n"
        "  \"cct_word\": \"0x%08x\",\n"
        "  \"auxiliary\": %.17g,\n"
        "  \"auxiliary_word\": \"0x%08x\",\n"
        "  \"converter_0_to_5\": \"0x%lx\"\n"
        "}\n",
        xy[0], xy[1], x_word, y_word, result[0], cct_word,
        result[1], auxiliary_word,
        (unsigned long)((uintptr_t)converter - base));
    dlclose(handle);
    return 0;
}
