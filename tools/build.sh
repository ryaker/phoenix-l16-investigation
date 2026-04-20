#!/bin/bash
# Build lri_process for x86_64 (required — library is Intel only)
# Runs under Rosetta 2 on Apple Silicon.
#
# Prerequisites:
#   Xcode Command Line Tools   (xcode-select --install)
#   macOS SDK with ImageIO     (included with CLT)
#
# Usage:
#   ./build.sh                 # compile
#   arch -x86_64 ./lri_process LRI/L16_00177.lri out.tiff

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRAMEWORKS="$SCRIPT_DIR/Lumen/Lumen.app/Contents/Frameworks"

# Verify the library exists
if [[ ! -f "$FRAMEWORKS/libcp.dylib" ]]; then
    echo "ERROR: libcp.dylib not found at:"
    echo "  $FRAMEWORKS/libcp.dylib"
    echo "Mount or copy Lumen.app into the Lumen/ subdirectory first."
    exit 1
fi

echo "Building lri_process (x86_64)..."

arch -x86_64 clang++ \
    -arch x86_64 \
    -std=c++17 \
    -stdlib=libc++ \
    -O2 \
    -L"$FRAMEWORKS" \
    -lcp \
    -Wl,-rpath,"$FRAMEWORKS" \
    -framework CoreFoundation \
    -framework CoreGraphics \
    -framework ImageIO \
    -framework CoreServices \
    -o "$SCRIPT_DIR/lri_process" \
    "$SCRIPT_DIR/lri_process.cpp"

echo "Build successful: $SCRIPT_DIR/lri_process"
echo ""
echo "Quick test:"
echo "  arch -x86_64 ./lri_process LRI/L16_00177.lri test_out.tiff"
echo ""
echo "If render() returns empty with profile=0, try:"
echo "  arch -x86_64 ./lri_process LRI/L16_00177.lri test_out.tiff --profile 1"
echo "  arch -x86_64 ./lri_process LRI/L16_00177.lri test_out.tiff --profile 2"
