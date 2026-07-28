"""classical.py - Hartree-Fock and FCI reference energies from PySCF."""

import numpy as np
from pyscf import fci, gto, scf

BOHR_PER_ANGSTROM = 1.8897261254578281


def classical_energies(r_angstrom, basis="sto-3g"):
    """Return (E_HF, E_FCI, E_nuclear_repulsion) for H2 at bond length r.

    All energies are TOTAL energies in Hartree, i.e. they already include
    the nuclear repulsion term.
    """
    mol = gto.M(
        atom=f"H 0 0 0; H 0 0 {r_angstrom}",
        basis=basis,
        unit="Angstrom",      # be explicit; PennyLane's default is Bohr
        verbose=0,
    )

    mf = scf.RHF(mol)
    e_hf = mf.kernel()
    if not mf.converged:
        print(f"  WARNING: SCF did not converge at r={r_angstrom}")

    e_fci = fci.FCI(mf).kernel()[0]

    return e_hf, e_fci, mol.energy_nuc()


def decomposition_check(r_angstrom=0.735):
    """Confirm that total = electronic + nuclear repulsion."""
    mol = gto.M(atom=f"H 0 0 0; H 0 0 {r_angstrom}", basis="sto-3g",
                unit="Angstrom", verbose=0)
    mf = scf.RHF(mol)
    e_total = mf.kernel()
    e_nuc = mol.energy_nuc()

    print(f"electronic only    {e_total - e_nuc:12.6f} Ha")
    print(f"nuclear repulsion  {e_nuc:12.6f} Ha")
    print(f"total              {e_total:12.6f} Ha")

    # Tolerance is 1e-6, not 1e-12: PySCF and this file use CODATA constants
    # from different revisions, which differ in the 10th significant figure.
    expected_nuc = 1.0 / (r_angstrom * BOHR_PER_ANGSTROM)
    assert abs(e_nuc - expected_nuc) < 1e-6, "nuclear repulsion mismatch"
    print(f"hand-computed 1/R  {expected_nuc:12.6f} Ha   OK")
    print(f"  (differ by {abs(e_nuc - expected_nuc):.2e} Ha - "
          f"different CODATA revisions, not a bug)")


def classical_scan(grid, basis="sto-3g", verbose=True):
    """HF and FCI across a range of bond lengths.

    Two thirds of the final figure, before any quantum code exists.
    """
    e_hf = np.zeros(len(grid))
    e_fci = np.zeros(len(grid))
    for i, r in enumerate(grid):
        e_hf[i], e_fci[i], _ = classical_energies(r, basis)
        if verbose:
            print(f"  r={r:5.3f}  HF={e_hf[i]:9.6f}  FCI={e_fci[i]:9.6f}")
    return e_hf, e_fci


if __name__ == "__main__":
    r = 0.735
    e_hf, e_fci, e_nuc = classical_energies(r)

    print(f"bond length          {r:12.4f} Angstrom")
    print(f"nuclear repulsion    {e_nuc:12.6f} Ha")
    print(f"Hartree-Fock         {e_hf:12.6f} Ha")
    print(f"FCI                  {e_fci:12.6f} Ha")
    print(f"correlation energy   {e_hf - e_fci:12.6f} Ha "
          f"({(e_hf - e_fci) * 27.2114:.4f} eV)")
    print()
    decomposition_check(r)
