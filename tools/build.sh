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
LOCAL_LUMEN_APP="$SCRIPT_DIR/Lumen/Lumen.app"
VERIFIED_LUMEN_APP="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app"

if [[ -n "${LUMEN_APP:-}" ]]; then
    LUMEN_APP_PATH="$LUMEN_APP"
elif [[ -d "$LOCAL_LUMEN_APP" ]]; then
    LUMEN_APP_PATH="$LOCAL_LUMEN_APP"
elif [[ -d "$VERIFIED_LUMEN_APP" ]]; then
    LUMEN_APP_PATH="$VERIFIED_LUMEN_APP"
else
    LUMEN_APP_PATH="$LOCAL_LUMEN_APP"
fi

FRAMEWORKS="$LUMEN_APP_PATH/Contents/Frameworks"

# Verify the library exists
if [[ ! -f "$FRAMEWORKS/libcp.dylib" ]]; then
    echo "ERROR: libcp.dylib not found at:"
    echo "  $FRAMEWORKS/libcp.dylib"
    echo "Set LUMEN_APP=/path/to/Lumen.app or mount/copy Lumen.app into tools/Lumen/."
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
