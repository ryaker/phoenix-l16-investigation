#include <errno.h>
#include <fcntl.h>
#include <mach-o/dyld.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

enum {
    kCallbackOffset = 0x346fd0,
    kCallbackStolenBytes = 18,
    kConvertOffset = 0xa9f20,
    kConvertReturnOffset = 0x3470be,
    kConvertStolenBytes = 20,
    kMapOffset = 0x80,
};

typedef void (*callback_fn)(void *);
typedef void (*convert_fn)(void *, const void *, const void *, const void *, int);

typedef struct {
    int32_t hue_divisions;
    int32_t saturation_divisions;
    int32_t value_divisions;
    uint32_t padding;
    void *begin;
    void *end;
    void *capacity;
} HSVMap;

static callback_fn original_callback;
static convert_fn original_convert;
static uintptr_t installed_base;
static pthread_once_t capture_once = PTHREAD_ONCE_INIT;
static pthread_once_t convert_capture_once = PTHREAD_ONCE_INIT;
static void *pending_payload;
static void *pending_destination;
static const void *pending_input_config;
static const void *pending_output_config;

static uintptr_t libcp_base(void) {
    for (uint32_t i = 0; i < _dyld_image_count(); ++i) {
        const char *name = _dyld_get_image_name(i);
        if (name != NULL && strstr(name, "/libcp.dylib") != NULL) {
            return (uintptr_t)_dyld_get_image_header(i);
        }
    }
    return 0;
}

static int write_all(const char *path, const void *data, size_t size) {
    int fd = open(path, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) {
        return 0;
    }
    const uint8_t *cursor = data;
    size_t remaining = size;
    while (remaining != 0) {
        ssize_t written = write(fd, cursor, remaining);
        if (written <= 0) {
            close(fd);
            return 0;
        }
        cursor += written;
        remaining -= (size_t)written;
    }
    return close(fd) == 0;
}

static void capture_map_once(void) {
    const char *map_path = getenv("L16_COLOR_MAP_OUT");
    const char *metadata_path = getenv("L16_COLOR_MAP_META");
    const char *owner_path = getenv("L16_COLOR_OWNER_OUT");
    void *owner = pending_payload == NULL ? NULL : *(void **)pending_payload;
    HSVMap *map = owner == NULL ? NULL : (HSVMap *)((uint8_t *)owner + kMapOffset);
    size_t size = 0;
    if (map != NULL && map->begin != NULL && map->end >= map->begin) {
        size = (size_t)((uint8_t *)map->end - (uint8_t *)map->begin);
    }
    int map_ok = map_path != NULL && size != 0 &&
        write_all(map_path, map->begin, size);
    int owner_ok = owner_path != NULL && owner != NULL &&
        write_all(owner_path, owner, 0x200);

    char metadata[1024];
    int length = snprintf(
        metadata, sizeof(metadata),
        "{\n"
        "  \"callback\": \"libcp+0x346fd0\",\n"
        "  \"payload\": \"%p\",\n"
        "  \"owner\": \"%p\",\n"
        "  \"map_object_offset\": \"0x80\",\n"
        "  \"dimensions\": [%d, %d, %d],\n"
        "  \"map_begin\": \"%p\",\n"
        "  \"map_end\": \"%p\",\n"
        "  \"map_capacity\": \"%p\",\n"
        "  \"map_size\": %zu,\n"
        "  \"map_write_ok\": %s,\n"
        "  \"owner_write_ok\": %s\n"
        "}\n",
        pending_payload, owner,
        map == NULL ? 0 : map->hue_divisions,
        map == NULL ? 0 : map->saturation_divisions,
        map == NULL ? 0 : map->value_divisions,
        map == NULL ? NULL : map->begin,
        map == NULL ? NULL : map->end,
        map == NULL ? NULL : map->capacity,
        size, map_ok ? "true" : "false", owner_ok ? "true" : "false");
    if (metadata_path != NULL && length > 0 && (size_t)length < sizeof(metadata)) {
        write_all(metadata_path, metadata, (size_t)length);
    }
    fprintf(stderr,
            "L16_COLOR_MAP_CAPTURE dims=%d,%d,%d bytes=%zu status=%s\n",
            map == NULL ? 0 : map->hue_divisions,
            map == NULL ? 0 : map->saturation_divisions,
            map == NULL ? 0 : map->value_divisions,
            size, map_ok ? "ok" : "failed");
}

static void capture_conversion_once(void) {
    const char *image_path = getenv("L16_COLOR_CONVERT_OUT");
    const char *metadata_path = getenv("L16_COLOR_CONVERT_META");
    const char *input_config_path = getenv("L16_COLOR_INPUT_CONFIG_OUT");
    const char *output_config_path = getenv("L16_COLOR_OUTPUT_CONFIG_OUT");
    const uint8_t *descriptor = pending_destination;
    int32_t width = descriptor == NULL ? 0 : *(const int32_t *)(descriptor + 0x10);
    int32_t height = descriptor == NULL ? 0 : *(const int32_t *)(descriptor + 0x14);
    int32_t stride = descriptor == NULL ? 0 : *(const int32_t *)(descriptor + 0x18);
    void *data = descriptor == NULL ? NULL : *(void *const *)(descriptor + 0x20);
    size_t size = width > 0 && height > 0 && stride >= width
        ? (size_t)stride * (size_t)height * 16
        : 0;
    int image_ok = image_path != NULL && data != NULL && size != 0 &&
        write_all(image_path, data, size);
    int input_ok = input_config_path != NULL && pending_input_config != NULL &&
        write_all(input_config_path, pending_input_config, 0x34);
    int output_ok = output_config_path != NULL && pending_output_config != NULL &&
        write_all(output_config_path, pending_output_config, 0x34);

    char metadata[1024];
    int length = snprintf(
        metadata, sizeof(metadata),
        "{\n"
        "  \"wrapper\": \"libcp+0xa9f20\",\n"
        "  \"caller_return\": \"libcp+0x3470be\",\n"
        "  \"destination_descriptor\": \"%p\",\n"
        "  \"input_config\": \"%p\",\n"
        "  \"output_config\": \"%p\",\n"
        "  \"width\": %d,\n"
        "  \"height\": %d,\n"
        "  \"stride_pixels\": %d,\n"
        "  \"image_size\": %zu,\n"
        "  \"image_write_ok\": %s,\n"
        "  \"input_config_write_ok\": %s,\n"
        "  \"output_config_write_ok\": %s\n"
        "}\n",
        pending_destination, pending_input_config, pending_output_config,
        width, height, stride, size,
        image_ok ? "true" : "false",
        input_ok ? "true" : "false",
        output_ok ? "true" : "false");
    if (metadata_path != NULL && length > 0 && (size_t)length < sizeof(metadata)) {
        write_all(metadata_path, metadata, (size_t)length);
    }
    fprintf(stderr,
            "L16_COLOR_CONVERT_CAPTURE image=%dx%d/%d bytes=%zu status=%s\n",
            width, height, stride, size, image_ok ? "ok" : "failed");
}

__attribute__((noinline)) static void callback_hook(void *payload) {
    pending_payload = payload;
    pthread_once(&capture_once, capture_map_once);
    original_callback(payload);
}

__attribute__((noinline)) static void convert_hook(
    void *destination, const void *source, const void *input_config,
    const void *output_config, int flag) {
    uintptr_t return_address = (uintptr_t)__builtin_return_address(0);
    original_convert(destination, source, input_config, output_config, flag);
    if (return_address == installed_base + kConvertReturnOffset) {
        pending_destination = destination;
        pending_input_config = input_config;
        pending_output_config = output_config;
        pthread_once(&convert_capture_once, capture_conversion_once);
    }
}

static void emit_absolute_jump(uint8_t *destination, const void *target) {
    destination[0] = 0x48;
    destination[1] = 0xb8;
    uintptr_t address = (uintptr_t)target;
    memcpy(destination + 2, &address, sizeof(address));
    destination[10] = 0xff;
    destination[11] = 0xe0;
}

static void *install_trampoline(uint8_t *entry, const uint8_t *expected,
                                size_t stolen_bytes, const void *hook) {
    if (memcmp(entry, expected, stolen_bytes) != 0) {
        return NULL;
    }
    const size_t page_size = (size_t)getpagesize();
    uint8_t *trampoline = mmap(NULL, page_size, PROT_READ | PROT_WRITE,
                               MAP_PRIVATE | MAP_ANON, -1, 0);
    if (trampoline == MAP_FAILED) {
        return NULL;
    }
    memcpy(trampoline, entry, stolen_bytes);
    emit_absolute_jump(trampoline + stolen_bytes, entry + stolen_bytes);
    if (mprotect(trampoline, page_size, PROT_READ | PROT_EXEC) != 0) {
        return NULL;
    }

    uintptr_t page = (uintptr_t)entry & ~(page_size - 1);
    if (mprotect((void *)page, page_size, PROT_READ | PROT_WRITE | PROT_EXEC) != 0) {
        return NULL;
    }
    emit_absolute_jump(entry, hook);
    memset(entry + 12, 0x90, stolen_bytes - 12);
    __builtin___clear_cache((char *)entry, (char *)entry + stolen_bytes);
    mprotect((void *)page, page_size, PROT_READ | PROT_EXEC);
    return trampoline;
}

__attribute__((constructor)) static void install_hook(void) {
    installed_base = libcp_base();
    if (installed_base == 0) {
        fprintf(stderr, "L16_COLOR_MAP_HOOK libcp_not_loaded\n");
        return;
    }
    const uint8_t callback_expected[kCallbackStolenBytes] = {
        0x55, 0x48, 0x89, 0xe5, 0x41, 0x57, 0x41, 0x56, 0x41,
        0x54, 0x53, 0x48, 0x81, 0xec, 0x80, 0x01, 0x00, 0x00,
    };
    const uint8_t convert_expected[kConvertStolenBytes] = {
        0x55, 0x48, 0x89, 0xe5, 0x41, 0x57, 0x41, 0x56, 0x41, 0x55,
        0x41, 0x54, 0x53, 0x48, 0x81, 0xec, 0xa8, 0x00, 0x00, 0x00,
    };
    original_callback = (callback_fn)install_trampoline(
        (uint8_t *)(installed_base + kCallbackOffset), callback_expected,
        sizeof(callback_expected), callback_hook);
    original_convert = (convert_fn)install_trampoline(
        (uint8_t *)(installed_base + kConvertOffset), convert_expected,
        sizeof(convert_expected), convert_hook);
    if (original_callback == NULL || original_convert == NULL) {
        fprintf(stderr, "L16_COLOR_MAP_HOOK install_failed errno=%d\n", errno);
        return;
    }
    fprintf(stderr, "L16_COLOR_MAP_HOOK installed libcp_base=0x%lx\n",
            (unsigned long)installed_base);
}
