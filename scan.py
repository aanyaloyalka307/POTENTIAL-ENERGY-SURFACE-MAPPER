"""scan.py - sweep the bond length and build the potential energy surface."""

import time

import numpy as np
from pennylane import numpy as pnp

from classical import classical_energies
from hamiltonian import qubit_hamiltonian
from vqe_single import build_uccsd, run_vqe


def make_grid():
    """Dense near the minimum, coarse in the tail.

    Rounding happens BEFORE np.unique, otherwise floating-point noise
    leaves near-duplicate points that survive de-duplication.
    """
    return np.unique(np.concatenate([
        np.arange(0.30, 0.60, 0.05),     # repulsive wall - coarse is fine
        np.arange(0.60, 0.95, 0.025),    # around the minimum - dense
        np.arange(0.95, 1.60, 0.05),     # rising towards dissociation
        np.arange(1.60, 2.55, 0.10),     # flat tail - coarse is fine
    ]).round(4))


def scan(grid=None, warm_start=True, verbose=True):
    """Run HF, FCI and VQE at every geometry on the grid."""
    if grid is None:
        grid = make_grid()

    n = len(grid)
    e_hf = np.zeros(n)
    e_fci = np.zeros(n)
    e_vqe = np.zeros(n)
    iterations = np.zeros(n, dtype=int)

    params = None
    t0 = time.time()

    for i, r in enumerate(grid):
        # 1. classical references at THIS geometry
        e_hf[i], e_fci[i], _ = classical_energies(r)

        # 2. REBUILD the Hamiltonian at THIS geometry.
        #    Reusing a stale one is a silent, hard-to-spot error.
        H, n_qubits = qubit_hamiltonian(r)

        ansatz, n_params = build_uccsd(n_qubits)

        # 3. WARM START: reuse the previous geometry's solution.
        if params is None or not warm_start:
            params = pnp.zeros(n_params, requires_grad=True)

        e_vqe[i], params, history = run_vqe(H, n_qubits, ansatz, params)
        iterations[i] = len(history)

        if verbose:
            print(f"  r={r:5.3f}  HF={e_hf[i]:9.6f}  FCI={e_fci[i]:9.6f}  "
                  f"VQE={e_vqe[i]:9.6f}  "
                  f"err={abs(e_vqe[i]-e_fci[i])*1e3:8.5f} mHa  "
                  f"{iterations[i]:4d} it")

    if verbose:
        print(f"\n{n} points in {time.time()-t0:.1f} s   "
              f"({iterations.sum()} optimiser iterations total)")

    return dict(grid=grid, e_hf=e_hf, e_fci=e_fci, e_vqe=e_vqe,
                iterations=iterations)


if __name__ == "__main__":
    import os
    os.makedirs("data", exist_ok=True)

    results = scan()
    np.savez("data/scan.npz", **results)
    print("saved data/scan.npz")

    err = np.abs(results["e_vqe"] - results["e_fci"]) * 1000
    print(f"\nmax VQE error across the scan: {err.max():.6f} mHa")

    # 0.01 mHa is 160x tighter than chemical accuracy (1.6 mHa) and still
    # leaves room for the residual that warm-starting propagates forward.
    assert err.max() < 0.01, "VQE deviates from FCI somewhere on the scan"
    print("scan verified against FCI at every geometry")
