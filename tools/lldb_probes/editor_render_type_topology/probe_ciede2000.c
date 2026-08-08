#include <dlfcn.h>
#include <inttypes.h>
#include <mach-o/dyld.h>
#include <stdint.h>
#include <stdio.h>
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

int main(void) {
    void *handle = dlopen(kLibcp, RTLD_NOW | RTLD_LOCAL);
    uintptr_t base = find_libcp_base();
    if (handle == NULL || base == 0) {
        fprintf(stderr, "failed to load libcp: %s\n", dlerror());
        return 1;
    }
    typedef double (*ciede_fn)(const void *, const double *, const double *);
    ciede_fn ciede = (ciede_fn)(base + 0x1273c0);
    static const double pairs[][6] = {
        {50.0, 2.6772, -79.7751, 50.0, 0.0, -82.7485},
        {50.0, 3.1571, -77.2803, 50.0, 0.0, -82.7485},
        {50.0, 2.8361, -74.0200, 50.0, 0.0, -82.7485},
        {50.0, -1.3802, -84.2814, 50.0, 0.0, -82.7485},
        {50.0, -1.1848, -84.8006, 50.0, 0.0, -82.7485},
        {50.0, -0.9009, -85.5211, 50.0, 0.0, -82.7485},
        {50.0, 0.0, 0.0, 50.0, -1.0, 2.0},
        {50.0, 2.49, -0.001, 50.0, -2.49, 0.001},
    };
    printf("{\n  \"helper\": \"0x1273c0\",\n  \"pairs\": [\n");
    for (size_t i = 0; i < sizeof(pairs) / sizeof(pairs[0]); ++i) {
        double value = ciede(NULL, pairs[i], pairs[i] + 3);
        uint64_t word;
        memcpy(&word, &value, sizeof(word));
        printf("    {\"value\": %.17g, \"word\": \"0x%016" PRIx64 "\"}%s\n",
               value, word,
               i + 1 == sizeof(pairs) / sizeof(pairs[0]) ? "" : ",");
    }
    printf("  ]\n}\n");
    dlclose(handle);
    return 0;
}
