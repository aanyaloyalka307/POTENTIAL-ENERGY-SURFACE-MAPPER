"""vqe_single.py - VQE at one fixed geometry, checked against FCI."""

import numpy as np
import pennylane as qml
from pennylane import numpy as pnp

from classical import classical_energies
from hamiltonian import ELECTRONS, qubit_hamiltonian


def build_uccsd(n_qubits, electrons=ELECTRONS, verbose=False):
    """Return (ansatz_fn, n_params) for a UCCSD circuit.

    The ansatz starts from the Hartree-Fock state and applies every single
    and double excitation available in this orbital space.

    verbose is off by default because Phase 4 calls this inside a loop.
    """
    singles, doubles = qml.qchem.excitations(electrons, n_qubits)
    s_wires, d_wires = qml.qchem.excitations_to_wires(singles, doubles)
    hf = qml.qchem.hf_state(electrons, n_qubits)

    if verbose:
        print(f"  reference state    {hf}")
        print(f"  single excitations {singles}")
        print(f"  double excitations {doubles}")

    def ansatz(params, wires):
        qml.UCCSD(params, wires, s_wires=s_wires, d_wires=d_wires,
                  init_state=hf)

    return ansatz, len(singles) + len(doubles)


def run_vqe(H, n_qubits, ansatz, params, stepsize=0.15,
            max_iter=400, tol=1e-9, verbose=False):
    """Minimise <psi(params)|H|psi(params)>.

    Converges on CHANGE IN ENERGY, not on a fixed iteration count.
    Returns (energy, params, history).
    """
    dev = qml.device("default.qubit", wires=n_qubits)

    @qml.qnode(dev, diff_method="backprop")
    def cost(p):
        ansatz(p, wires=range(n_qubits))
        return qml.expval(H)

    opt = qml.AdamOptimizer(stepsize=stepsize)
    history = []
    e_prev = np.inf

    for i in range(max_iter):
        params, energy = opt.step_and_cost(cost, params)
        history.append(float(energy))
        if verbose and i % 20 == 0:
            print(f"    iter {i:4d}   E = {energy:.10f} Ha")
        if abs(energy - e_prev) < tol:
            break
        e_prev = energy

    return float(cost(params)), params, history


def main(r_angstrom=0.735):
    print(f"VQE for H2 at {r_angstrom} Angstrom\n")

    e_hf, e_fci, _ = classical_energies(r_angstrom)
    H, n_qubits = qubit_hamiltonian(r_angstrom)
    print(f"  qubits             {n_qubits}")

    ansatz, n_params = build_uccsd(n_qubits, verbose=True)
    print(f"  free parameters    {n_params}\n")

    params = pnp.zeros(n_params, requires_grad=True)
    energy, params, history = run_vqe(H, n_qubits, ansatz, params,
                                      verbose=True)

    print()
    print(f"  Hartree-Fock       {e_hf:14.8f} Ha")
    print(f"  VQE                {energy:14.8f} Ha")
    print(f"  FCI (exact)        {e_fci:14.8f} Ha")
    print(f"  VQE error          {abs(energy - e_fci) * 1000:14.8f} mHa")
    print(f"  correlation found  "
          f"{(e_hf - energy) / (e_hf - e_fci) * 100:13.4f} %")
    print(f"  iterations         {len(history):14d}")
    print(f"  optimal parameters {np.round(params, 6)}")

    assert energy >= e_fci - 1e-9, "below FCI - variational principle violated"
    assert abs(energy - e_fci) < 1e-6, "VQE did not reach chemical accuracy"
    print("\n  VQE verified against FCI")
    return energy


if __name__ == "__main__":
    main()
