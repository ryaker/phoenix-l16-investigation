// Replay the admitted Phoenix HighlightRestore kernel over one full-frame capture.
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <algorithm>
#include <string>
#include <vector>

#include "depth/highlight_restore.h"

using phoenix::premerge::RawPlaneU16;

static std::vector<std::uint16_t> load(const char* path, std::size_t count) {
    std::vector<std::uint16_t> values(count);
    FILE* file = std::fopen(path, "rb");
    if (!file || std::fread(values.data(), sizeof(std::uint16_t), count, file) != count) {
        std::fprintf(stderr, "cannot read %s\n", path);
        std::exit(2);
    }
    std::fclose(file);
    return values;
}

int main(int argc, char** argv) {
    if (argc != 8) {
        std::fprintf(stderr, "usage: %s input expected red_x red_y c0 c2 boundary\n", argv[0]);
        return 2;
    }
    constexpr int width = 4160;
    constexpr int height = 3120;
    constexpr std::size_t count = static_cast<std::size_t>(width) * height;
    RawPlaneU16 original;
    original.width = width;
    original.height = height;
    original.phase.red_x = std::atoi(argv[3]);
    original.phase.red_y = std::atoi(argv[4]);
    original.data = load(argv[1], count);
    const std::vector<std::uint16_t> expected = load(argv[2], count);
    phoenix::depth::HighlightRestoreParams parameters;
    parameters.c[0] = std::strtof(argv[5], nullptr);
    parameters.c[1] = 1.0f;
    parameters.c[2] = std::strtof(argv[6], nullptr);
    const std::string boundary = argv[7];
    constexpr int pad = 4;
    RawPlaneU16 input = original;
    if (boundary != "none") {
        input.width = width + 2 * pad;
        input.height = height + 2 * pad;
        input.phase = original.phase;
        input.data.resize(static_cast<std::size_t>(input.width) * input.height);
        auto map = [&](int coordinate, int extent) {
            if (0 <= coordinate && coordinate < extent) return coordinate;
            if (boundary == "edge") return std::clamp(coordinate, 0, extent - 1);
            if (boundary == "reflect") return coordinate < 0 ? -coordinate : 2 * extent - 2 - coordinate;
            if (boundary == "symmetric") return coordinate < 0 ? -coordinate - 1 : 2 * extent - 1 - coordinate;
            if (boundary == "parity") return phoenix::premerge::clampParity(coordinate, extent);
            return -1;
        };
        for (int y = 0; y < input.height; ++y) {
            const int source_y = map(y - pad, height);
            for (int x = 0; x < input.width; ++x) {
                const int source_x = map(x - pad, width);
                input.data[static_cast<std::size_t>(y) * input.width + x] =
                    source_x < 0 || source_y < 0 ? 0 : original.at(source_x, source_y);
            }
        }
    }
    const RawPlaneU16 restored = phoenix::depth::highlightRestore(input, parameters);
    std::size_t equal = 0;
    std::size_t changed = 0;
    std::uint16_t max_difference = 0;
    for (std::size_t index = 0; index < count; ++index) {
        const int y = static_cast<int>(index / width);
        const int x = static_cast<int>(index % width);
        const std::uint16_t actual = boundary == "none"
            ? restored.data[index]
            : restored.data[static_cast<std::size_t>(y + pad) * input.width + x + pad];
        equal += actual == expected[index];
        changed += actual != original.data[index];
        const std::uint16_t difference = actual > expected[index]
            ? actual - expected[index]
            : expected[index] - actual;
        if (difference > max_difference) max_difference = difference;
    }
    std::printf("colorfusion_highlight_join boundary=%s equal=%zu/%zu changed=%zu maxdiff=%u\n",
                boundary.c_str(), equal, count, changed, max_difference);
    return equal == count ? 0 : 1;
}
