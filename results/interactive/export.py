"""export.py - dump data/landscape.npz to the JSON the web page reads."""
import json
import pathlib

import numpy as np

ROOT = pathlib.Path(__file__).parent.parent.parent
d = np.load(ROOT / "data/landscape.npz")
sc = np.load(ROOT / "data/scan.npz")
R, TH, Z = d["R"], d["TH"], d["Z"]

out = {
    "R":  [round(float(x), 4) for x in R],
    "TH": [round(float(x), 5) for x in TH],
    "Z":  [[round(float(v), 5) for v in row] for row in Z],
    "theta_star": [round(float(x), 5) for x in TH[Z.argmin(axis=0)]],
    "e_star":     [round(float(x), 6) for x in Z.min(axis=0)],
    "scan": {"R":   [round(float(x), 4) for x in sc["grid"]],
             "hf":  [round(float(x), 6) for x in sc["e_hf"]],
             "fci": [round(float(x), 6) for x in sc["e_fci"]]},
}
p = pathlib.Path(__file__).parent / "landscape.json"
p.write_text(json.dumps(out, separators=(",", ":")))
print(f"wrote {p.name} ({p.stat().st_size/1024:.1f} KB)")
