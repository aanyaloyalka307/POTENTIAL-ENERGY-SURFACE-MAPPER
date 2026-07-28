#!/bin/bash
# Shared launcher for the React 3D web viewer, used by both
# Run_VQE_Scan.command and Run_3D_Viewer.command.
#
#   open_web_viewer.sh            build only if it has never been built
#   open_web_viewer.sh --rebuild  re-bake the data and rebuild (fresh results)
#
# It serves the built page locally (works in every browser) and opens it,
# then waits so closing the Terminal window stops the server.
set -u
cd "$(dirname "$0")"

DIST="web/dist/index.html"
REBUILD="${1:-}"
HAVE_NPM=false
command -v npm >/dev/null 2>&1 && HAVE_NPM=true

# Decide whether we need to (re)build.
need_build=false
[ ! -f "$DIST" ] && need_build=true
[ "$REBUILD" = "--rebuild" ] && $HAVE_NPM && need_build=true

if $need_build; then
    if ! $HAVE_NPM; then
        if [ -f "$DIST" ]; then
            echo "Node.js not found - opening the existing build instead."
        else
            echo "ERROR: Node.js / npm was not found, and the viewer has not"
            echo "been built yet. Install Node from https://nodejs.org/ and retry."
            read -p "Press Enter to close this window..."
            exit 1
        fi
    else
        echo "Preparing the 3D web viewer..."
        # Re-bake the surface from the latest data when the env + grid exist.
        if [ -x ".venv/bin/python" ] && [ -f "data/landscape.npz" ]; then
            ".venv/bin/python" export_web.py
        fi
        if [ ! -d "web/node_modules" ]; then
            echo "Installing web dependencies (first time only, ~30 s)..."
            ( cd web && npm install ) || {
                echo "ERROR: npm install failed."
                read -p "Press Enter to close this window..."
                exit 1
            }
        fi
        ( cd web && npm run build ) || {
            echo "ERROR: the web build failed."
            read -p "Press Enter to close this window..."
            exit 1
        }
    fi
fi

# Serve locally and open, or fall back to opening the file directly.
PORT=8799
if command -v python3 >/dev/null 2>&1; then
    ( cd web/dist && python3 -m http.server "$PORT" >/dev/null 2>&1 ) &
    SERVER_PID=$!
    trap 'kill $SERVER_PID 2>/dev/null' EXIT
    sleep 1
    URL="http://localhost:$PORT/index.html"
    echo ""
    echo "============================================================"
    echo " 3D viewer running at  $URL"
    echo "============================================================"
    open "$URL"
else
    open "$DIST"
fi

echo ""
echo "Drag to orbit, scroll to zoom. Continuation / Random start / Wireframe /"
echo "Reset view are along the bottom; light/dark toggle is top-right."
echo ""
read -p "Press Enter here to stop the viewer and close this window..."
