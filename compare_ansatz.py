"""compare_ansatz.py - UCCSD against a hardware-efficient ansatz.

The experiment: run the same scan, same Hamiltonian and same optimiser with
two different circuits, and find out where they diverge.
"""

import numpy as np
import pennylane as qml
from pennylane import numpy as pnp

from classical import classical_energies
from hamiltonian import ELECTRONS, qubit_hamiltonian
from scan import make_grid
from vqe_single import build_uccsd, run_vqe

CHEMICAL_ACCURACY = 1.6e-3    # Hartree


def build_hea(n_qubits, reps=2, electrons=ELECTRONS):
    """Hardware-efficient ansatz: RY/RZ rotations plus a CNOT ladder.

    This is the PennyLane equivalent of Qiskit's
    TwoLocal(rotation_blocks=["ry","rz"], entanglement_blocks="cx").

    It is applied on top of the Hartree-Fock reference state so that the
    comparison with UCCSD isolates the CIRCUIT rather than the starting
    point. Note it does NOT conserve particle number - nothing in its
    structure knows about chemistry.
    """
    hf = qml.qchem.hf_state(electrons, n_qubits)
    n_params = 2 * n_qubits * (reps + 1)

    def ansatz(params, wires):
        qml.BasisState(hf, wires=wires)
        p = params.reshape(reps + 1, n_qubits, 2)
        for layer in range(reps):
            for q in range(n_qubits):
                qml.RY(p[layer, q, 0], wires=q)
                qml.RZ(p[layer, q, 1], wires=q)
            for q in range(n_qubits - 1):
                qml.CNOT(wires=[q, q + 1])
        for q in range(n_qubits):
            qml.RY(p[reps, q, 0], wires=q)
            qml.RZ(p[reps, q, 1], wires=q)

    return ansatz, n_params


def _best_of(H, n_qubits, ansatz, n_params, n_restarts=3, seed0=0, scale=0.3):
    """Cold start: best energy over several random initialisations."""
    best = np.inf
    for s in range(n_restarts):
        rng = np.random.default_rng(seed0 + s)
        p0 = pnp.array(rng.normal(0, scale, n_params), requires_grad=True)
        e, _, _ = run_vqe(H, n_qubits, ansatz, p0, max_iter=800)
        best = min(best, e)
    return best


def compare(grid=None):
    """UCCSD vs hardware-efficient, warm and cold, across the whole curve."""
    if grid is None:
        grid = make_grid()

    n = len(grid)
    out = {k: np.zeros(n) for k in
           ["e_fci", "uccsd", "hea_warm", "hea_cold", "hea_deep"]}

    p_uccsd = p_hea = None

    for i, r in enumerate(grid):
        _, out["e_fci"][i], _ = classical_energies(r)
        H, nq = qubit_hamiltonian(r)

        anz_u, np_u = build_uccsd(nq)
        if p_uccsd is None:
            p_uccsd = pnp.zeros(np_u, requires_grad=True)
        out["uccsd"][i], p_uccsd, _ = run_vqe(H, nq, anz_u, p_uccsd)

        anz_h, np_h = build_hea(nq, reps=2)
        if p_hea is None:
            rng = np.random.default_rng(7)
            p_hea = pnp.array(rng.normal(0, 0.05, np_h), requires_grad=True)
        out["hea_warm"][i], p_hea, _ = run_vqe(H, nq, anz_h, p_hea,
                                               max_iter=600)

        out["hea_cold"][i] = _best_of(H, nq, anz_h, np_h, seed0=1000)

        anz_d, np_d = build_hea(nq, reps=4)
        out["hea_deep"][i] = _best_of(H, nq, anz_d, np_d, seed0=2000)

        print(f"  r={r:5.3f}  UCCSD={_mha(out['uccsd'][i], out['e_fci'][i])}"
              f"  HEA warm={_mha(out['hea_warm'][i], out['e_fci'][i])}"
              f"  HEA cold={_mha(out['hea_cold'][i], out['e_fci'][i])}"
              f"  HEA deep={_mha(out['hea_deep'][i], out['e_fci'][i])}",
              flush=True)

    out["grid"] = grid
    return out


def _mha(e, ref):
    return f"{abs(e - ref) * 1000:8.4f} mHa"


def diagnose(r=2.5, n_restarts=8, depths=(1, 2, 3, 4, 6)):
    """Why does the hardware-efficient ansatz fail at long bond length?

    Two explanations, which are NOT mutually exclusive:
      - OPTIMISER TRAPPING -> many restarts pile up on one non-optimal value
      - EXPRESSIBILITY     -> even the BEST restart cannot reach the answer

    Do not use the spread (peak-to-peak) as the test: a single lucky restart
    that escapes a dominant basin inflates it and inverts the verdict. The
    two statistics that actually separate the cases are the size of the
    modal cluster and the best energy found over all restarts.
    """
    _, e_fci, _ = classical_energies(r)
    H, nq = qubit_hamiltonian(r)

    print(f"\nrandom restarts at r={r} A   (FCI = {e_fci:.6f} Ha)")
    energies = []
    for s in range(n_restarts):
        anz, npar = build_hea(nq, reps=2)
        rng = np.random.default_rng(100 + s)
        p0 = pnp.array(rng.normal(0, 0.5, npar), requires_grad=True)
        e, _, _ = run_vqe(H, nq, anz, p0, max_iter=800)
        energies.append(e)
        print(f"  restart {s}:  {e:.6f}  ({abs(e-e_fci)*1000:7.3f} mHa)")

    energies = np.array(energies)
    best = energies.min()
    rounded = np.round(energies, 6)
    values, counts = np.unique(rounded, return_counts=True)
    modal_value = values[counts.argmax()]
    modal_count = counts.max()

    print(f"\n  distinct minima found : {len(values)}")
    print(f"  modal cluster         : {modal_value:.6f} Ha "
          f"({modal_count}/{n_restarts} restarts)")
    print(f"  best over all restarts: {best:.6f} Ha "
          f"({abs(best-e_fci)*1000:.3f} mHa)")

    trapped = modal_count >= 0.5 * n_restarts and modal_value > best + 1e-6
    print("  ->", "dominant attractor basin: most restarts are TRAPPED"
          if trapped else "no dominant basin: restarts explore freely")

    # Random restarts bound what random SEARCH finds - not what the circuit
    # can EXPRESS. To separate those you must reach the same geometry by a
    # path the optimiser can actually follow. Continuation does that.
    e_cont = continuation(r, reps=2)
    print(f"  same circuit via continuation: {e_cont:.6f} Ha "
          f"({abs(e_cont-e_fci)*1000:.3f} mHa)")

    if abs(e_cont - e_fci) < CHEMICAL_ACCURACY:
        print("  -> NOT an expressibility limit. The solution is inside this")
        print("     circuit's reach; random initialisation simply never")
        print("     finds it. The failure is the optimisation landscape.")
    elif abs(best - e_fci) > CHEMICAL_ACCURACY:
        print("  -> neither random search nor continuation reaches chemical")
        print("     accuracy: an expressibility limit is likely, though not")
        print("     proven - only more initialisation strategies can rule")
        print("     it in.")

    print(f"\ncircuit depth at r={r} A   (best of 3 cold starts each)")
    for reps in depths:
        anz, npar = build_hea(nq, reps=reps)
        best_d = _best_of(H, nq, anz, npar, n_restarts=3, seed0=200)
        print(f"  reps={reps} ({npar:2d} params):  {best_d:.6f}  "
              f"({abs(best_d-e_fci)*1000:7.3f} mHa)"
              + ("   < chemical accuracy"
                 if abs(best_d - e_fci) < CHEMICAL_ACCURACY else ""))


def continuation(r_target=2.5, reps=2, start=0.30, step=0.05):
    """Reach r_target by walking there from an easy geometry.

    This is the control for the restart experiment. If continuation gets a
    result random restarts cannot, the circuit was always expressive enough
    and the problem is purely where the optimiser starts.
    """
    path = np.round(np.arange(start, r_target + 1e-9, step), 4)
    params = None
    energy = None
    for r in path:
        H, nq = qubit_hamiltonian(float(r))
        anz, npar = build_hea(nq, reps=reps)
        if params is None:
            rng = np.random.default_rng(7)
            params = pnp.array(rng.normal(0, 0.05, npar), requires_grad=True)
        energy, params, _ = run_vqe(H, nq, anz, params, max_iter=600)
    return energy


if __name__ == "__main__":
    import os
    os.makedirs("data", exist_ok=True)

    results = compare()
    np.savez("data/ansatz_comparison.npz", **results)
    print("\nsaved data/ansatz_comparison.npz")

    for key in ["uccsd", "hea_warm", "hea_cold", "hea_deep"]:
        err = np.abs(results[key] - results["e_fci"])
        n_bad = int((err > CHEMICAL_ACCURACY).sum())
        print(f"  {key:10s} max err {err.max()*1000:9.4f} mHa   "
              f"{n_bad:2d}/{len(err)} geometries above chemical accuracy")

    diagnose()
