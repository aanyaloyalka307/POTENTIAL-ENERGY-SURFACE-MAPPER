#!/bin/bash
# Double-click this file to run the whole project end to end.
# It sets up its own private Python environment the first time.

# Move into the folder this file lives in, no matter where it is opened from.
cd "$(dirname "$0")"

echo "============================================================"
echo " H2 Potential Energy Surface with VQE"
echo "============================================================"
echo ""

# --- 1. find a working python3 -------------------------------------------
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
else
    echo "ERROR: Python 3 was not found on this computer."
    echo "Install it from https://www.python.org/downloads/ and try again."
    echo ""
    read -p "Press Enter to close this window..."
    exit 1
fi
echo "Using $($PYTHON --version)"
echo ""

# --- 2. set up a private environment so nothing else is touched ----------
if [ ! -d ".venv" ]; then
    echo "First run - creating a private Python environment (.venv)..."
    "$PYTHON" -m venv .venv || {
        echo ""
        echo "ERROR: could not create the environment."
        read -p "Press Enter to close this window..."
        exit 1
    }
fi

VENV_PY=".venv/bin/python"
[ -x "$VENV_PY" ] || VENV_PY=".venv/Scripts/python.exe"   # Windows layout

echo "Checking the scientific libraries (slow only the first time)..."
"$VENV_PY" -c "import pennylane, pyscf, numpy, scipy, matplotlib" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing libraries, please wait a few minutes..."
    "$VENV_PY" -m pip install --quiet --upgrade pip
    "$VENV_PY" -m pip install --quiet -r requirements.txt || {
        echo ""
        echo "ERROR: failed to install the libraries."
        echo "If pyscf was the problem, you may need a C compiler:"
        echo "  macOS:  xcode-select --install"
        echo "  Ubuntu: sudo apt install build-essential"
        echo ""
        read -p "Press Enter to close this window..."
        exit 1
    }
fi
echo ""

# --- 3. verify the setup reproduces known-correct energies ---------------
echo "------------------------------------------------------------"
echo " Step 1 of 3 - verifying the setup"
echo "------------------------------------------------------------"
"$VENV_PY" verify_env.py || {
    echo ""
    echo "ERROR: the environment check failed. Nothing later will be"
    echo "trustworthy, so stopping here. See TROUBLE in HOW_TO_RUN.txt."
    read -p "Press Enter to close this window..."
    exit 1
}
echo ""

# --- 4. the scan ---------------------------------------------------------
echo "------------------------------------------------------------"
echo " Step 2 of 4 - scanning 43 bond lengths (about 2 minutes)"
echo "------------------------------------------------------------"
echo "No output appears until it finishes. This is normal."
"$VENV_PY" scan.py || {
    echo ""
    echo "ERROR: the scan failed."
    read -p "Press Enter to close this window..."
    exit 1
}
echo ""

# --- 5. analysis, figure and the results spreadsheet --------------------
echo "------------------------------------------------------------"
echo " Step 3 of 4 - extracting the physics"
echo "------------------------------------------------------------"
"$VENV_PY" analyse.py || {
    echo ""
    echo "ERROR: the analysis failed."
    read -p "Press Enter to close this window..."
    exit 1
}

# Build the interactive surface grid the viewer needs (~25 s, first run
# only - it is cached in data/landscape.npz afterwards).
"$VENV_PY" landscape.py || {
    echo ""
    echo "ERROR: building the interactive surface failed."
    read -p "Press Enter to close this window..."
    exit 1
}

# Append this run's key numbers to results/run_history.xlsx so they are
# saved instead of only scrolling past above.
echo ""
echo "Recording this run's values to the spreadsheet..."
"$VENV_PY" export_results.py

FIGURE="results/figures/dissociation_curve.png"
HISTORY="results/run_history.xlsx"
[ -f "$HISTORY" ] || HISTORY="results/run_history.csv"
echo ""
echo "============================================================"
echo " Done. Figure:      $FIGURE"
echo "       Run history: $HISTORY"
echo "============================================================"

# --- 6. open the interactive 3D web viewer ------------------------------
echo ""
echo "------------------------------------------------------------"
echo " Step 4 of 4 - opening the interactive 3D viewer in your browser"
echo "------------------------------------------------------------"
# Hand off to the shared launcher: it re-bakes the surface from the results
# just computed, rebuilds the web page, serves it, and opens your browser.
# (The desktop matplotlib viewer is still available via: make viewer)
exec bash open_web_viewer.sh --rebuild
