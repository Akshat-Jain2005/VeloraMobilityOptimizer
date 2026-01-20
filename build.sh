#!/bin/bash
# Build script for VeloraMobilityOptimizer

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${PROJECT_DIR}/build"

echo "======================================"
echo "VeloraMobilityOptimizer Build System"
echo "======================================"

# Create build directory
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

echo "✓ Build directory: ${BUILD_DIR}"

# Configure with CMake
echo ""
echo "Configuring CMake..."
cmake -DCMAKE_BUILD_TYPE=Release "${PROJECT_DIR}"

# Build
echo ""
echo "Building project..."
cmake --build . --config Release --parallel $(nproc 2>/dev/null || echo 4)

echo ""
echo "======================================"
echo "✓ Build complete!"
echo "======================================"
echo ""
echo "Output binaries:"
[ -f "${BUILD_DIR}/solver/velora_solver" ] && echo "  • Solver: ${BUILD_DIR}/solver/velora_solver"

echo ""
echo "Usage:"
echo "  ./build/solver/velora_solver <input.json> <output.json>"
echo ""
