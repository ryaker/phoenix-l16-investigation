#include <array>
#include <bit>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "merge/colorfusion.h"

namespace {

std::vector<float> readFloats(const char* path) {
    std::ifstream input(path, std::ios::binary | std::ios::ate);
    if (!input) throw std::runtime_error("cannot open input");
    const auto size = input.tellg();
    input.seekg(0);
    std::vector<float> values(static_cast<std::size_t>(size) / sizeof(float));
    input.read(reinterpret_cast<char*>(values.data()), size);
    return values;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc != 5) {
        std::fprintf(stderr, "usage: %s source.bin reference.bin noiseScale m0,m1,m2\n", argv[0]);
        return 2;
    }
    const auto source = readFloats(argv[1]);
    const auto reference = readFloats(argv[2]);
    if (source.size() != 1024 || reference.size() != 1024) return 3;
    std::array<float, 256> sourceLane0{}, referenceLane0{};
    for (std::size_t i = 0; i < 256; ++i) {
        sourceLane0[i] = source[4 * i];
        referenceLane0[i] = reference[4 * i];
    }
    const float noise = std::stof(argv[3]);
    const float module = phoenix::merge::colorModuleRetention(
        sourceLane0, referenceLane0, noise, true
    );
    std::printf("phoenix_module_m=%.9g/0x%08x\n", module, std::bit_cast<std::uint32_t>(module));

    std::vector<float> m;
    std::string csv = argv[4];
    std::size_t start = 0;
    while (start <= csv.size()) {
        const auto end = csv.find(',', start);
        m.push_back(std::stof(csv.substr(start, end - start)));
        if (end == std::string::npos) break;
        start = end + 1;
    }
    const float f = phoenix::merge::colorFusionWeight(m.data(), static_cast<int>(m.size()));
    std::printf("phoenix_combine_f=%.9g/0x%08x\n", f, std::bit_cast<std::uint32_t>(f));
    return 0;
}
