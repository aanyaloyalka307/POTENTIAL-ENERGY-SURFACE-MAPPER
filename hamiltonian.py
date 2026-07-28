"""hamiltonian.py - build the qubit Hamiltonian for H2 at any geometry."""

import numpy as np
import pennylane as qml

BOHR_PER_ANGSTROM = 1.8897261254578281
SYMBOLS = ["H", "H"]
ELECTRONS = 2


def qubit_hamiltonian(r_angstrom, basis="sto-3g", mapping="jordan_wigner"):
    """Return (H, n_qubits) for H2 with the nuclei r_angstrom apart.

    PennyLane's qchem module expects coordinates in BOHR, not Angstrom.
    Getting this wrong is the single most expensive bug in the project,
    so the conversion is done explicitly and in one place.
    """
    r_bohr = r_angstrom * BOHR_PER_ANGSTROM

    coordinates = np.array([
        0.0, 0.0, 0.0,        # H atom 1 at the origin
        0.0, 0.0, r_bohr,     # H atom 2 along z
    ])

    H, n_qubits = qml.qchem.molecular_hamiltonian(
        SYMBOLS,
        coordinates,
        basis=basis,
        mapping=mapping,
    )
    return H, n_qubits


def verify_against_fci(r_angstrom=0.735):
    """Exact-diagonalise the qubit Hamiltonian and compare with PySCF FCI."""
    from classical import classical_energies

    _, e_fci, _ = classical_energies(r_angstrom)

    H, n = qubit_hamiltonian(r_angstrom)
    matrix = qml.matrix(H, wire_order=range(n))

    # The qubit Hamiltonian spans ALL electron numbers, 0 through n.
    # Project onto the 2-electron sector to get the chemical ground state.
    occupation = np.array([bin(k).count("1") for k in range(2 ** n)])
    sector = np.where(occupation == ELECTRONS)[0]
    sub = matrix[np.ix_(sector, sector)]

    e_sector = np.linalg.eigvalsh(sub)[0].real
    e_global = np.linalg.eigvalsh(matrix)[0].real

    print(f"PySCF FCI                     {e_fci:12.8f} Ha")
    print(f"qubit H, 2-electron sector    {e_sector:12.8f} Ha")
    print(f"qubit H, all sectors          {e_global:12.8f} Ha")
    print(f"difference                    {abs(e_sector - e_fci):12.2e} Ha")

    assert abs(e_sector - e_fci) < 1e-8, "qubit Hamiltonian does NOT match FCI"
    print("\nqubit Hamiltonian verified against FCI")


def compare_mappings(r_angstrom=0.735):
    for mapping in ["jordan_wigner", "parity", "bravyi_kitaev"]:
        H, n = qubit_hamiltonian(r_angstrom, mapping=mapping)
        M = qml.matrix(H, wire_order=range(n))
        print(f"{mapping:16s} qubits={n}  terms={len(H.terms()[0]):3d}  "
              f"ground state={np.linalg.eigvalsh(M)[0].real:.6f}")


def tapered_hamiltonian(r_angstrom=0.735):
    """Reduce the qubit count using the Hamiltonian's Z2 symmetries."""
    H, n = qubit_hamiltonian(r_angstrom)

    generators = qml.symmetry_generators(H)      # the conserved quantities
    paulix_ops = qml.paulix_ops(generators, n)   # the corresponding rotations
    sector = qml.qchem.optimal_sector(H, generators, ELECTRONS)

    H_tapered = qml.taper(H, generators, paulix_ops, sector)

    print(f"symmetry generators found  {len(generators)}")
    print(f"optimal sector             {sector}")
    print(f"qubits  {n} -> {len(H_tapered.wires)}")
    print(f"terms   {len(H.terms()[0])} -> {len(H_tapered.terms()[0])}")

    M = qml.matrix(H_tapered, wire_order=H_tapered.wires)
    print(f"ground state after tapering  "
          f"{np.linalg.eigvalsh(M)[0].real:.8f} Ha")
    return H_tapered


if __name__ == "__main__":
    H, n = qubit_hamiltonian(0.735)
    coeffs, ops = H.terms()
    print(f"qubits      {n}")
    print(f"Pauli terms {len(coeffs)}")
    print()
    for c, op in list(zip(coeffs, ops))[:6]:
        print(f"  {c:+.8f}   {op}")
    print("  ...")
    print()
    verify_against_fci()
    print()
    compare_mappings()
    print()
    tapered_hamiltonian()
