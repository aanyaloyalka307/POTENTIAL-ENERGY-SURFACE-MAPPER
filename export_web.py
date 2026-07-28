"""export_web.py - dump the landscape/scan grids to JSON for the web viewer.

The React + react-three-fiber viewer in web/ is a self-contained static app:
it has no Python backend, so the surface it draws has to be baked out here and
imported at build time. This reads the same artifacts the desktop viewer uses
and writes web/src/data/landscape.json.

    python landscape.py      # writes data/landscape.npz (~25 s, first time)
    python export_web.py     # writes web/src/data/landscape.json
"""

import json
import os

import numpy as np

LANDSCAPE = "data/landscape.npz"
SCAN = "data/scan.npz"
OUT = "web/src/data/landscape.json"

# Matches viewer.squash / landscape.ZTOP: the repulsive wall dwarfs the valley,
# so the wall is recorded but the display-facing consumer compresses it. We ship
# the RAW energies; the client squashes for geometry and keeps raw for readouts.
ZTOP = 0.40


def main():
    if not os.path.exists(LANDSCAPE):
        raise SystemExit(f"{LANDSCAPE} not found - run `python landscape.py` first.")

    d = np.load(LANDSCAPE)
    R, TH, Z = d["R"], d["TH"], d["Z"]        # Z shape: (nTheta, nR)

    theta_idx = Z.argmin(axis=0)              # valley floor index per geometry
    theta_star = TH[theta_idx]
    e_star = Z.min(axis=0)

    # Exact (FCI) reference per landscape geometry, interpolated from the scan
    # grid so the client can report "distance from exact" at every R.
    fci_on_R = None
    if os.path.exists(SCAN):
        s = np.load(SCAN)
        fci_on_R = np.interp(R, s["grid"], s["e_fci"])

    payload = {
        "R": [round(float(r), 4) for r in R],
        "TH": [round(float(t), 5) for t in TH],
        # round to keep the JSON small without touching displayed precision
        "Z": [[round(float(z), 5) for z in row] for row in Z],
        "valley": {
            "thetaStar": [round(float(t), 5) for t in theta_star],
            "eStar": [round(float(e), 6) for e in e_star],
        },
        "fciOnR": None if fci_on_R is None
        else [round(float(e), 6) for e in fci_on_R],
        "meta": {
            "nR": int(len(R)),
            "nTheta": int(len(TH)),
            "rMin": float(R[0]), "rMax": float(R[-1]),
            "thetaMin": float(TH[0]), "thetaMax": float(TH[-1]),
            "zMin": float(Z.min()), "zTop": ZTOP,
            "thetaDrift": round(float(abs(theta_star[-1] - theta_star[0])), 3),
        },
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(payload, f, separators=(",", ":"))

    size_kb = os.path.getsize(OUT) / 1024
    print(f"wrote {OUT}  ({size_kb:.0f} KB)")
    print(f"  grid {payload['meta']['nR']} R x {payload['meta']['nTheta']} theta, "
          f"theta* drift {payload['meta']['thetaDrift']} rad")


if __name__ == "__main__":
    main()
