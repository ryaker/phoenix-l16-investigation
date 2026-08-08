// hr_cxx_check.cpp — verify the Phoenix C++ highlight-restore port against the
// six Lumen ground-truth tile pairs captured under lldb on L16_03041.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#include "depth/highlight_restore.h"

using phoenix::premerge::RawPlaneU16;

struct Tile { int idx, w, h, py, px; float c0, c2; };

static const Tile kTiles[] = {
    {0, 590, 462, 1, 1, 0.5555472373962402f, 0.6055743098258972f},
    {1, 626, 456, 1, 1, 0.555017352104187f,  0.5953865051269531f},
    {2, 450, 630, 0, 0, 0.5426871180534363f, 0.591360330581665f},
    {3, 618, 474, 1, 1, 0.555017352104187f,  0.5953865051269531f},
    {4, 468, 626, 0, 0, 0.5426871180534363f, 0.591360330581665f},
    {5, 678, 680, 1, 1, 0.5568259358406067f, 0.6148008704185486f},
};

static std::vector<std::uint16_t> load(const std::string& p, std::size_t n) {
    std::vector<std::uint16_t> v(n);
    FILE* f = std::fopen(p.c_str(), "rb");
    if (!f) { std::fprintf(stderr, "open %s\n", p.c_str()); std::exit(1); }
    if (std::fread(v.data(), 2, n, f) != n) {
        std::fprintf(stderr, "short read %s\n", p.c_str()); std::exit(1);
    }
    std::fclose(f);
    return v;
}

int main(int argc, char** argv) {
    const std::string dir = argc > 1 ? argv[1] : "runs/highlight_restore/tiles";
    for (const Tile& t : kTiles) {
        char sb[512], db[512];
        std::snprintf(sb, sizeof(sb), "%s/tile%02d_src.u16", dir.c_str(), t.idx);
        std::snprintf(db, sizeof(db), "%s/tile%02d_dst.u16", dir.c_str(), t.idx);
        const std::size_t n = static_cast<std::size_t>(t.w) * t.h;
        RawPlaneU16 src;
        src.width = t.w; src.height = t.h;
        src.phase.red_x = t.px; src.phase.red_y = t.py;
        src.data = load(sb, n);
        const std::vector<std::uint16_t> dst = load(db, n);

        phoenix::depth::HighlightRestoreParams prm;
        prm.c[0] = t.c0; prm.c[1] = 1.0f; prm.c[2] = t.c2;
        const RawPlaneU16 got = phoenix::depth::highlightRestore(src, prm);

        // Compare only the interior the kernel actually writes (margin 4).
        long tot = 0, ex = 0, le1 = 0, mx = 0, chg = 0;
        for (int y = 4; y < t.h - 4; ++y)
            for (int x = 4; x < t.w - 4; ++x) {
                const std::size_t i = static_cast<std::size_t>(y) * t.w + x;
                const long a = got.data[i], b = dst[i];
                const long d = a > b ? a - b : b - a;
                ++tot;
                if (d == 0) ++ex;
                if (d <= 1) ++le1;
                if (d > mx) mx = d;
                if (dst[i] != src.data[i]) ++chg;
            }
        std::printf("tile%d %dx%d phase=[%d,%d]  exact=%.4f%%  |d|<=1=%.4f%%"
                    "  maxdiff=%ld  changed=%ld/%ld\n",
                    t.idx, t.w, t.h, t.py, t.px,
                    100.0 * ex / tot, 100.0 * le1 / tot, mx, chg, tot);
    }
    return 0;
}
