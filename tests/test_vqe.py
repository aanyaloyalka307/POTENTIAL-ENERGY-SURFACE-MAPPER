"""VQE convergence tests. Slower than test_physics.py - each runs a solver."""

import numpy as np
import pytest
from pennylane import numpy as pnp

from classical import classical_energies
from compare_ansatz import build_hea
from hamiltonian import qubit_hamiltonian
from vqe_single import build_uccsd, run_vqe

CHEMICAL_ACCURACY = 1.6e-3


@pytest.fixture(scope="module")
def equilibrium():
    r = 0.735
    _, e_fci, _ = classical_energies(r)
    H, n = qubit_hamiltonian(r)
    return r, e_fci, H, n


def test_uccsd_parameter_count(equilibrium):
    """H2 in a minimal basis: 2 singles + 1 double."""
    _, _, _, n = equilibrium
    _, n_params = build_uccsd(n)
    assert n_params == 3


def test_uccsd_reaches_fci(equilibrium):
    _, e_fci, H, n = equilibrium
    ansatz, n_params = build_uccsd(n)
    energy, _, _ = run_vqe(H, n, ansatz, pnp.zeros(n_params,
                                                   requires_grad=True))
    assert abs(energy - e_fci) < 1e-6


def test_variational_principle_holds(equilibrium):
    """VQE can never legitimately go below the true ground state."""
    _, e_fci, H, n = equilibrium
    ansatz, n_params = build_uccsd(n)
    energy, _, _ = run_vqe(H, n, ansatz, pnp.zeros(n_params,
                                                   requires_grad=True))
    assert energy >= e_fci - 1e-9


def test_optimiser_starts_from_hartree_fock(equilibrium):
    """Zero parameters must mean the HF state, not something arbitrary."""
    r, _, H, n = equilibrium
    e_hf, _, _ = classical_energies(r)
    ansatz, n_params = build_uccsd(n)
    _, _, history = run_vqe(H, n, ansatz,
                            pnp.zeros(n_params, requires_grad=True))
    assert history[0] == pytest.approx(e_hf, abs=1e-6)


def test_singles_vanish_by_symmetry(equilibrium):
    """Only the double excitation does real work for H2."""
    _, _, H, n = equilibrium
    ansatz, n_params = build_uccsd(n)
    _, params, _ = run_vqe(H, n, ansatz, pnp.zeros(n_params,
                                                   requires_grad=True))
    p = np.asarray(params)
    assert abs(p[0]) < 1e-3
    assert abs(p[1]) < 1e-3
    assert abs(p[2]) > 0.1


def test_uccsd_recovers_all_correlation_energy(equilibrium):
    r, e_fci, H, n = equilibrium
    e_hf, _, _ = classical_energies(r)
    ansatz, n_params = build_uccsd(n)
    energy, _, _ = run_vqe(H, n, ansatz, pnp.zeros(n_params,
                                                   requires_grad=True))
    recovered = (e_hf - energy) / (e_hf - e_fci)
    assert recovered == pytest.approx(1.0, abs=1e-4)


@pytest.mark.parametrize("r", [0.5, 1.0, 2.0])
def test_uccsd_matches_fci_away_from_equilibrium(r):
    _, e_fci, _ = classical_energies(r)
    H, n = qubit_hamiltonian(r)
    ansatz, n_params = build_uccsd(n)
    energy, _, _ = run_vqe(H, n, ansatz, pnp.zeros(n_params,
                                                   requires_grad=True))
    assert abs(energy - e_fci) < CHEMICAL_ACCURACY / 100


# ----------------------------------------------------------------------
# Phase 6 - the headline result
# ----------------------------------------------------------------------
def test_hea_parameter_count():
    _, n_params = build_hea(4, reps=2)
    assert n_params == 24


def test_hea_cold_start_fails_at_long_bond_length():
    """The Phase 6 result: random initialisation misses at 2.5 A."""
    r = 2.5
    _, e_fci, _ = classical_energies(r)
    H, n = qubit_hamiltonian(r)
    ansatz, n_params = build_hea(n, reps=2)

    best = np.inf
    for seed in range(3):
        rng = np.random.default_rng(1000 + seed)
        p0 = pnp.array(rng.normal(0, 0.3, n_params), requires_grad=True)
        e, _, _ = run_vqe(H, n, ansatz, p0, max_iter=800)
        best = min(best, e)

    assert abs(best - e_fci) > CHEMICAL_ACCURACY


def test_continuation_rescues_the_same_circuit():
    """...and the same circuit succeeds when reached by continuation.

    This is the control that proves the failure is the optimisation
    landscape and NOT an expressibility limit.
    """
    from compare_ansatz import continuation

    _, e_fci, _ = classical_energies(2.5)
    e_cont = continuation(2.5, reps=2, start=0.5, step=0.1)
    assert abs(e_cont - e_fci) < CHEMICAL_ACCURACY
