#include <mach-o/dyld.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

typedef void (*worker_fn)(void *, void *, int32_t, int32_t, void *);

typedef struct {
    void *object;
    uint32_t stereo_index;
    uint32_t active;
    uint32_t max_active;
    uint64_t first_thread;
    uint64_t second_thread;
} ObjectState;

static uintptr_t libcp_base;
static void *worker_trampoline;
static pthread_mutex_t state_mutex = PTHREAD_MUTEX_INITIALIZER;
static ObjectState objects[64];
static uint32_t object_count;
static uint32_t total_calls;
static uint32_t global_active;
static uint32_t global_max_active;

static uintptr_t find_libcp_base(void) {
    for (uint32_t i = 0; i < _dyld_image_count(); ++i) {
        const char *name = _dyld_get_image_name(i);
        if (name != NULL && strstr(name, "/libcp.dylib") != NULL)
            return (uintptr_t)_dyld_get_image_header(i);
    }
    return 0;
}

static void write_absolute_jump(uint8_t *destination, const void *target) {
    destination[0] = 0x48;
    destination[1] = 0xb8;
    uintptr_t address = (uintptr_t)target;
    memcpy(destination + 2, &address, sizeof(address));
    destination[10] = 0xff;
    destination[11] = 0xe0;
}

static void make_writable(void *address) {
    long page_size = sysconf(_SC_PAGESIZE);
    uintptr_t page = (uintptr_t)address & ~((uintptr_t)page_size - 1);
    if (mprotect((void *)page, (size_t)page_size,
                 PROT_READ | PROT_WRITE | PROT_EXEC) != 0)
        abort();
}

static void *install_hook(uintptr_t va, size_t copied, const void *hook) {
    uint8_t *entry = (uint8_t *)(libcp_base + va);
    uint8_t *trampoline = mmap(NULL, 4096, PROT_READ | PROT_WRITE | PROT_EXEC,
                               MAP_PRIVATE | MAP_ANON, -1, 0);
    if (trampoline == MAP_FAILED) return NULL;
    memcpy(trampoline, entry, copied);
    write_absolute_jump(trampoline + copied, entry + copied);
    make_writable(entry);
    write_absolute_jump(entry, hook);
    memset(entry + 12, 0x90, copied - 12);
    __builtin___clear_cache((char *)entry, (char *)entry + copied);
    return trampoline;
}

static ObjectState *state_for_object(void *object) {
    for (uint32_t i = 0; i < object_count; ++i)
        if (objects[i].object == object) return &objects[i];
    if (object_count >= 64) return NULL;
    ObjectState *state = &objects[object_count++];
    state->object = object;
    memcpy(&state->stereo_index, (uint8_t *)object + 8, sizeof(state->stereo_index));
    return state;
}

__attribute__((noinline))
static void worker_hook(void *object, void *tile, int32_t step,
                        int32_t direction, void *context) {
    uint64_t thread_id = 0;
    pthread_threadid_np(NULL, &thread_id);

    pthread_mutex_lock(&state_mutex);
    ObjectState *state = state_for_object(object);
    ++total_calls;
    ++global_active;
    if (global_active > global_max_active) global_max_active = global_active;
    if (state != NULL) {
        ++state->active;
        if (state->active > state->max_active) state->max_active = state->active;
        if (state->first_thread == 0) state->first_thread = thread_id;
        else if (state->first_thread != thread_id && state->second_thread == 0)
            state->second_thread = thread_id;
    }
    pthread_mutex_unlock(&state_mutex);

    ((worker_fn)worker_trampoline)(object, tile, step, direction, context);

    pthread_mutex_lock(&state_mutex);
    if (state != NULL) --state->active;
    --global_active;
    pthread_mutex_unlock(&state_mutex);
}

__attribute__((visibility("default")))
void l16_write_mode8_overlap_report(void) {
    const char *path = getenv("L16_MODE8_OVERLAP_REPORT");
    if (path == NULL) return;
    pthread_mutex_lock(&state_mutex);
    FILE *output = fopen(path, "w");
    if (output != NULL) {
        fprintf(output, "total_calls=%u\nglobal_max_active=%u\nobjects=%u\n",
                total_calls, global_max_active, object_count);
        for (uint32_t i = 0; i < object_count; ++i) {
            fprintf(output,
                    "object[%u]=0x%llx stereo_index=%u max_active=%u first_thread=%llu second_thread=%llu\n",
                    i, (unsigned long long)(uintptr_t)objects[i].object,
                    objects[i].stereo_index, objects[i].max_active,
                    (unsigned long long)objects[i].first_thread,
                    (unsigned long long)objects[i].second_thread);
        }
        fclose(output);
    }
    pthread_mutex_unlock(&state_mutex);
}

__attribute__((constructor))
static void install_worker_hook(void) {
    libcp_base = find_libcp_base();
    if (libcp_base == 0) return;
    worker_trampoline = install_hook(0x276860, 12, (const void *)&worker_hook);
}
