#!/bin/bash
# Double-click to open the interactive React + WebGL 3D landscape viewer.
# Builds it the first time (needs Node.js), then just serves and opens it.
# For a full re-run of the science first, use Run_VQE_Scan.command instead.

cd "$(dirname "$0")"

echo "============================================================"
echo " PES Explorer - interactive 3D optimisation landscape"
echo "============================================================"
echo ""

exec bash open_web_viewer.sh
