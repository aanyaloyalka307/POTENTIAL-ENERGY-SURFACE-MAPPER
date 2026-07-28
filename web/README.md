# PES Explorer — React 3D web viewer

An interactive, "playable" version of the optimisation-landscape surface
`E(R, θ)`, built with **React + react-three-fiber (Three.js)** and animated with
**Motion (Framer Motion)**. It is the web counterpart to the desktop
`viewer.py`: same data, same physics, orbit-able in a browser.

![the viewer](../results/figures/optimisation_landscape.png)

## What you can do

- **Orbit / zoom** the viridis energy surface (drag, scroll).
- **Scrub** the bond length `R` and watch the point ride the valley floor.
- **Continuation** — animate the walk from a short bond out to full
  dissociation, staying on `θ*(R)` the whole way.
- **Random start** — drop a blind guess at the stretched geometry and see how
  far it lands from the exact (FCI) answer, in millihartree.
- **Wireframe** / **Reset view**.
- **Light / dark toggle** (top-right) — adapts the UI and the 3D scene
  (background, fog, grid, accent colours); defaults to your system preference
  and remembers your choice.

The right-hand readout reports `R`, `θ`, energy, and the distance from exact.

## Run it

Easiest — from the project root, double-click **`Run_3D_Viewer.command`**.

Or by hand:

```bash
# from the project root
python export_web.py          # bakes data/landscape.npz -> web/src/data/landscape.json
cd web
npm install
npm run build                 # -> web/dist/index.html  (one self-contained file)
python3 -m http.server 8799 --directory dist
# open http://localhost:8799
```

Development, with hot reload:

```bash
cd web && npm run dev
```

## How it is wired

- `export_web.py` (project root) reads `data/landscape.npz` + `data/scan.npz`
  and writes `src/data/landscape.json` — the surface, the valley floor, and the
  FCI reference per geometry.
- `src/lib/surface.js` maps physical `(R, θ, E)` into a world box, compresses
  the repulsive wall for display (matching `viewer.squash`), and builds the
  buffer geometry with viridis vertex colours.
- `src/Scene.jsx` — the Three.js scene: surface, valley line, glowing marker
  (which lerps to its target each frame for smooth travel), lights, orbit
  controls, and a camera rig that flies home on **Reset view**.
- `src/App.jsx` — state + the Motion-animated overlay (`ui/Dock.jsx`,
  `ui/Readout.jsx`).

## Notes

- The build is a **single self-contained `index.html`** (data inlined), so it is
  portable and needs no backend. Fonts load from Google Fonts and fall back to
  system fonts offline.
- To refresh the surface after re-running the science, re-run `export_web.py`
  and `npm run build` (or `make web` from the project root).
