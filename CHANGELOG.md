# Development record

Not a release changelog — this project has no versions to track. It is the
build log, kept because several entries record defects that were found and
fixed during construction, and how they were found.

The fixes themselves all live in the code: the grid bug is a regression test,
the tolerance reasoning is a comment in `scan.py`, the fit-window trap is a
docstring in `analyse.py`, and the honest warm-start measurement is in
`docs/Phase4_The_Geometry_Scan.pdf`. What follows is the order it happened in.

All entries dated 2026-07-27, except the viewer port (2026-07-28).

---

## Four defects found by running the project end to end (2026-07-28)

Ran the whole thing from `make clean`: verify, tests, scan, analyse, landscape,
viewer, anticommute demo. The physics all reproduced — 43 points, max VQE error
0.001257 mHa, R_e 0.7367 Å, θ* drifting 1.257 rad — and both committed figures
regenerated bit-identically. Four things around the edges did not hold up.

**A test that guards the headline claim had never run in CI.**
`test_landscape_valley_floor_moves_with_geometry` skips itself when
`data/landscape.npz` is missing. `data/` is gitignored, CI checks out fresh, and
the workflow never ran `landscape.py` — so on every CI run it skipped, reporting
`34 passed, 1 skipped`, which reads as green. Its own docstring says the whole
Phase 6 result rests on the drift it checks. CI now builds the grid first, and
treats *any* skip as a failure: a test that stops guarding something should not
be able to do it quietly.

**`make setup && make test` could not work on a clean machine.** `pytest` was
never in `requirements.txt`, and nothing there pulls it in transitively. CI
passed only because it installs `pytest` explicitly on its own line. Anyone
following HOW_TO_RUN hit `ModuleNotFoundError`. Added to `requirements.txt`.

**The launcher still claimed 44 bond lengths.** The grid-size correction below
reached the README, `ABOUT.txt` and `HOW_TO_RUN.txt`, but missed
`Run_VQE_Scan.command`. It is 43.

**Two documents still claimed 31 tests.** The suite has been 35 since the
Phase 6 work; the entry below already said so. `ABOUT.txt` and `HOW_TO_RUN.txt`
did not.

---

## The interactive viewer moved to Python (2026-07-28)

The landscape viewer was a self-contained WebGL page: a template, an inlined
copy of three.js, and a 678 KB generated `landscape_3d.html`. It worked, but it
meant the repository was 93% HTML by Linguist's count, and it carried a vendored
graphics library to draw one surface.

`viewer.py` replaces all of it with matplotlib, which was already a dependency.
Same four controls — Continuation, Random start, Wireframe, Reset view — same
slider, same readout, and the same log-compressed z-axis above the 0.40 Ha knee,
so the repulsive wall still reads as a wall instead of a flat tabletop.

Two things changed in the port. The viewer now opens a window rather than a
browser tab, so it needs the project's `.venv` where the old page needed nothing
but a double-click. And it reads `data/landscape.npz` directly, which removed
the `export.py` → `landscape.json` → `build.py` chain entirely.

One defect was caught during the port: the slider handle only followed the
walker during playback, so moving the walker any other way left the handle
stranded at its old index. It now syncs wherever the walker is driven from.

---

## Corrections, in brief

Four defects shipped before being caught. Each is listed in full below.

| What was wrong | How it was found |
|---|---|
| Phase 4's example output contained **invented energies** for r = 0.300 and 0.350 | Ran the launcher end to end; its first output line disagreed with the document |
| Two PDF listings shipped **assertion tolerances that fail when run** | Executed every listing rather than reading it |
| The grid was **43 points, documented as 44** — and every figure was plotted from a dataset with 1.6 Å duplicated | Printed the full scan output instead of the tail; the row count didn't match |
| The Phase 6 conclusion was **wrong twice** before it was right | Kept testing the hypothesis instead of the first plausible reading |

---

## Initial implementation

**H₂ potential energy surface with VQE, verified against exact diagonalisation**

Builds the full quantum-chemistry pipeline from nuclear geometry through
molecular integrals, the fermionic Hamiltonian and the fermion-to-qubit
mapping to a variational solution and extracted physical observables. No
hardcoded Pauli coefficients: the qubit Hamiltonian is generated at every
geometry, which is what makes the geometry scan possible.

Results (STO-3G, 0.30–2.50 Å):

- VQE/UCCSD reproduces FCI to within 0.0013 mHa everywhere, ~1000× tighter
  than chemical accuracy, recovering 100% of the correlation energy at
  equilibrium
- Extracted R<sub>e</sub> = 0.7367 Å (−0.63% vs experiment),
  D<sub>e</sub> = 5.556 eV (+17.1%), ω = 5184 cm⁻¹ (+17.8%); the energetic
  disagreement is the minimal basis, not the algorithm

Extension — ansatz comparison across dissociation:

- A hardware-efficient circuit (TwoLocal-equivalent, 2 repetitions) fails by
  up to 24 mHa at every geometry from 1.80 Å outward when randomly
  initialised, i.e. exactly where Hartree–Fock diverges
- 30 random restarts at 2.5 Å find 13 distinct minima and never reach
  chemical accuracy, which *looks* like an expressibility limit
- It is not: the same circuit reached by continuation along the dissociation
  coordinate reproduces FCI exactly. The failure is the optimisation
  landscape, not the circuit. `diagnose()` therefore runs the continuation
  control alongside the restart study, because restarts bound what random
  *search* finds rather than what a circuit can *express*

Includes 31 regression tests asserting the physics, CI on Python 3.11/3.12,
and seven roadmap PDFs covering theory and build guidance.

---

## Plain-text docs and a launcher — and the first corrections

Adds the beginner-facing entry points from the earlier project so the two
repositories read as the same author: `ABOUT.txt`, `HOW_TO_RUN.txt`, and a
double-click launcher.

**Corrections found while testing the launcher end to end:**

- Phase 4's abbreviated scan output contained **invented energies** for
  r = 0.300 and r = 0.350. Replaced with the real values from `scan.py`.
- Phase 1 Listing 1.2 and Phase 4 Listing 4.3 shipped **assertion tolerances
  that fail when run** (1e-10 on a CODATA-limited comparison, and 1e-3 mHa
  against a 1.257e-3 mHa residual). Both corrected, with the reasoning for
  the chosen threshold added.
- Phase 5 Listing 5.3 still defaulted to the old figure path.
- Phase 6 Listing 6.3 still carried the superseded docstring, and §2.3 still
  recommended the restart-spread test that the phase's own results disprove.
- Warm-start saving re-measured with `scan.py` itself rather than a separate
  harness: 5722 vs 6019 iterations, **4.9% not 4.7%**.

All 22 code listings across the seven PDFs now parse cleanly.

---

## Remove `smoketest.pdf`

A PDF-toolkit test artifact copied into `docs/` by mistake.

---

## Rename the launcher to `Run_VQE_Scan.command`

Follows the `Run_VQE_*.command` pattern of the earlier project so the two
repositories read as the same author, while staying accurate: this one runs a
bond-length scan rather than opening an app window.

---

## Correct the grid size: 43 geometries, not 44

The scan grid concatenates four `np.arange` ranges. Because `arange`
endpoints are inexact, 1.60 appeared as both `1.5999999999` and `1.6`, and
`np.unique` kept both. The fix — round *before* de-duplicating — landed in
`scan.py` earlier, but the figure data had already been generated with the
buggy grid and was never regenerated.

Consequence: every figure was plotted from 44 rows with 1.6 duplicated, and
"44 geometries" was wrong in the README, `ABOUT.txt`, `HOW_TO_RUN.txt` and
four of the seven PDFs. Visually nothing changed, since the duplicate points
overlapped exactly — but **the shipped code did not produce the shipped
data**, which defeats the reproducibility the project claims.

- Regenerated the figure data from the corrected grid: 43 rows, 43 unique
- Regenerated all 9 data-driven figures and rebuilt all 7 PDFs
- Corrected 19 occurrences of the count across docs and PDFs

Every headline result is unchanged: max VQE error 0.0013 mHa, the
hardware-efficient cold start still fails at exactly the 8 geometries from
1.80 Å outward, and the observables are identical. Only the denominator
moved, from /44 to /43.

Adds three regression tests that would have caught it:
`test_grid_has_no_duplicate_geometries`, `test_grid_size_and_span`,
`test_grid_is_denser_near_the_minimum`. Suite → 34 tests.

---

## `landscape.py` — the E(R, θ) surface behind the Phase 6 result

The dissociation curve is energy against one variable, so it is a curve and
rendering it in three dimensions would add nothing but decoration. There *is*
a genuine surface in this problem though: the energy as a function of **both**
the geometry and the ansatz parameter.

Plotting it explains the Phase 6 finding rather than merely illustrating it.
The valley floor — the optimal θ at each geometry — drifts smoothly from
0.105 rad at 0.30 Å to 1.361 rad at 2.50 Å, a movement of 1.257 rad across
the scan. Continuation enters that valley where the problem is easy and rides
it out to full dissociation. A random start at 2.5 Å is a blind guess along a
vertical line with no reason to land near θ\* = 1.36.

Added as Figure 6.4 to `Phase6_Ansatz_Comparison.pdf`, plus one regression
test asserting the drift is large and smooth — the entire continuation
argument rests on it. Suite → 35 tests.

---

## Interactive WebGL version of the landscape

matplotlib's 3D renderer has no real lighting and sorts faces with the
painter's algorithm, so a surface this folded reads poorly. This renders the
same grid in WebGL instead, self-contained at 662 KB with no external
requests, so it works offline and inside a strict CSP.

Interaction is in service of the argument rather than decoration: pressing
**Continuation** walks a marker along the valley floor from 0.30 Å to 2.50 Å
while the readout tracks its error against FCI, and **Random start** drops a
marker at a blind θ at 2.50 Å so you can watch it miss.

Three rendering details worth recording, each found by looking at the output
rather than by reasoning about it:

- A hard clip of the repulsive wall renders as a flat fake tabletop; an
  exponential soft-clip saturates and looks the same. Logarithmic compression
  above the knee keeps the wall rising and reads correctly.
- Axis sprites with `depthTest` disabled paint straight through the surface.
  They need real depth testing to sit in the scene.
- The camera has to back off in a portrait viewport or the surface overflows
  the sides.

---

## Rename to POTENTIAL-ENERGY-SURFACE-MAPPER

Matches the naming convention of GROUND-STATE-ENERGY-PREDICTOR — descriptive
caps naming a thing the project does — rather than stacking three acronyms.
