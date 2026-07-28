"""Physics regression tests.

These assert values that are properties of the physics, not of the software.
If any of them fail after a dependency upgrade, the dependency is wrong,
not the test.
"""

import numpy as np
import pennylane as qml
import pytest

from analyse import (BOHR_PER_ANGSTROM, dissociation_limit, fit_minimum,
                     harmonic_frequency, well_depth)
from classical import classical_energies
from hamiltonian import ELECTRONS, qubit_hamiltonian, tapered_hamiltonian

R_EQ = 0.735

# reference values, STO-3G
E_HF = -1.116999
E_FCI = -1.137306
E_NUC = 0.719969
E_DISSOC = -0.933164


# ----------------------------------------------------------------------
# Phase 1 - classical baseline
# ----------------------------------------------------------------------
def test_hartree_fock_energy():
    e_hf, _, _ = classical_energies(R_EQ)
    assert e_hf == pytest.approx(E_HF, abs=1e-6)


def test_fci_energy():
    _, e_fci, _ = classical_energies(R_EQ)
    assert e_fci == pytest.approx(E_FCI, abs=1e-6)


def test_fci_is_below_hartree_fock():
    """Correlation energy is strictly negative - FCI can only improve on HF."""
    e_hf, e_fci, _ = classical_energies(R_EQ)
    assert e_fci < e_hf


def test_nuclear_repulsion_is_one_over_r():
    """Total = electronic + 1/R. Catches inherited electronic-only energies."""
    _, _, e_nuc = classical_energies(R_EQ)
    expected = 1.0 / (R_EQ * BOHR_PER_ANGSTROM)
    # tolerance is loose: PySCF uses a different CODATA revision
    assert e_nuc == pytest.approx(expected, abs=1e-6)
    assert e_nuc == pytest.approx(E_NUC, abs=1e-6)


def test_correlation_energy_grows_as_bond_breaks():
    """Static correlation: the HF/FCI gap widens with separation."""
    _, _, _ = classical_energies(R_EQ)
    gaps = []
    for r in (0.735, 1.5, 2.5):
        e_hf, e_fci, _ = classical_energies(r)
        gaps.append(e_hf - e_fci)
    assert gaps[0] < gaps[1] < gaps[2]


# ----------------------------------------------------------------------
# Phase 2 - the qubit Hamiltonian
# ----------------------------------------------------------------------
def test_qubit_count_and_terms():
    H, n = qubit_hamiltonian(R_EQ)
    assert n == 4
    assert len(H.terms()[0]) == 15


def test_qubit_hamiltonian_reproduces_fci():
    """The gate on Phase 3: exact diagonalisation must match PySCF."""
    _, e_fci, _ = classical_energies(R_EQ)
    H, n = qubit_hamiltonian(R_EQ)
    matrix = qml.matrix(H, wire_order=range(n))

    occupation = np.array([bin(k).count("1") for k in range(2 ** n)])
    sector = np.where(occupation == ELECTRONS)[0]
    sub = matrix[np.ix_(sector, sector)]

    assert np.linalg.eigvalsh(sub)[0].real == pytest.approx(e_fci, abs=1e-8)


@pytest.mark.parametrize("mapping",
                         ["jordan_wigner", "parity", "bravyi_kitaev"])
def test_mappings_give_identical_spectra(mapping):
    """Mappings are unitary changes of basis - the physics cannot change."""
    H, n = qubit_hamiltonian(R_EQ, mapping=mapping)
    M = qml.matrix(H, wire_order=range(n))
    assert np.linalg.eigvalsh(M)[0].real == pytest.approx(E_FCI, abs=1e-6)


def test_tapering_preserves_ground_state():
    H_t = tapered_hamiltonian(R_EQ)
    assert len(H_t.wires) == 1
    M = qml.matrix(H_t, wire_order=H_t.wires)
    assert np.linalg.eigvalsh(M)[0].real == pytest.approx(E_FCI, abs=1e-6)


def test_hamiltonian_actually_depends_on_geometry():
    """Guards against the stale-Hamiltonian bug in Phase 4."""
    H1, _ = qubit_hamiltonian(0.735)
    H2, _ = qubit_hamiltonian(1.500)
    c1 = np.array(H1.terms()[0])
    c2 = np.array(H2.terms()[0])
    assert not np.allclose(c1, c2)


def test_bohr_conversion_constant():
    assert BOHR_PER_ANGSTROM == pytest.approx(1.8897261, abs=1e-6)


# ----------------------------------------------------------------------
# Phase 4 - the grid
# ----------------------------------------------------------------------
def test_grid_has_no_duplicate_geometries():
    """np.arange endpoints are inexact, so concatenating adjacent ranges can
    leave both 1.5999999999 and 1.6. Rounding must happen BEFORE np.unique.
    Getting that order wrong silently duplicates a geometry."""
    from scan import make_grid
    g = make_grid()
    assert len(g) == len(np.unique(g)), "grid contains a duplicated geometry"


def test_grid_size_and_span():
    from scan import make_grid
    g = make_grid()
    assert len(g) == 43
    assert g[0] == pytest.approx(0.30)
    assert g[-1] == pytest.approx(2.50)


def test_grid_is_denser_near_the_minimum():
    """Resolution is allocated by what each region is for."""
    from scan import make_grid
    g = make_grid()
    near = np.diff(g[(g >= 0.60) & (g <= 0.95)])
    tail = np.diff(g[g >= 1.60])
    assert near.max() < tail.min()


# ----------------------------------------------------------------------
# Phase 5 - analysis
# ----------------------------------------------------------------------
def test_fit_minimum_recovers_a_known_parabola():
    """Synthetic check: exact answer known analytically."""
    r = np.linspace(0.6, 0.9, 13)
    e = 3.0 * (r - 0.7412) ** 2 - 1.5
    r_eq, e_min, _ = fit_minimum(r, e, window=3)
    assert r_eq == pytest.approx(0.7412, abs=1e-6)
    assert e_min == pytest.approx(-1.5, abs=1e-9)


def test_fitted_minimum_lies_between_grid_points():
    """The whole point of fitting: do not quantise to the grid."""
    r = np.array([0.70, 0.725, 0.75, 0.775, 0.80])
    e = 2.0 * (r - 0.7367) ** 2 - 1.1
    r_eq, _, _ = fit_minimum(r, e, window=2)
    assert r_eq not in r


def test_dissociation_limit_is_two_hydrogen_atoms():
    assert dissociation_limit() == pytest.approx(E_DISSOC, abs=1e-6)


def test_curve_is_still_bound_at_the_last_grid_point():
    """Why analyse.py does not use e[-1] as the asymptote."""
    _, e_fci, _ = classical_energies(2.5)
    assert e_fci < dissociation_limit()
    assert (e_fci - dissociation_limit()) * 1000 == pytest.approx(-2.9,
                                                                  abs=0.2)


def test_harmonic_frequency_unit_conversion():
    """Skipping the Angstrom-to-Bohr step costs a factor of 1.8897^2."""
    coeffs = np.array([2.0, -3.0, 1.0])          # a = 2 Ha/A^2
    omega = harmonic_frequency(coeffs)
    wrong = omega * BOHR_PER_ANGSTROM            # sqrt of the squared factor
    assert wrong / omega == pytest.approx(1.8897261, abs=1e-6)
    assert omega > 0


def test_well_depth_sign():
    d_ha, d_ev = well_depth(e_min=-1.1373, e_asymptote=-0.9332)
    assert d_ha > 0
    assert d_ev == pytest.approx(d_ha * 27.2114, rel=1e-4)


# ----------------------------------------------------------------------
# The E(R, theta) landscape
# ----------------------------------------------------------------------
def test_landscape_valley_floor_moves_with_geometry():
    """The premise of continuation: theta* drifts smoothly with R.

    If the optimal parameter did NOT move, warm-starting would be pointless
    and a random start would be no worse. The whole Phase 6 result rests on
    this drift being real and large.
    """
    import os
    if not os.path.exists("data/landscape.npz"):
        pytest.skip("run `python landscape.py` first")

    d = np.load("data/landscape.npz")
    theta_star = d["TH"][d["Z"].argmin(axis=0)]

    # it moves a long way ...
    assert abs(theta_star[-1] - theta_star[0]) > 1.0
    # ... and it moves smoothly, never jumping between basins
    assert np.abs(np.diff(theta_star)).max() < 0.15
