"""analyse.py - extract physical observables from the scan and plot it."""

import os

import matplotlib.pyplot as plt
import numpy as np
from pyscf import gto, scf

BOHR_PER_ANGSTROM = 1.8897261254578281
HARTREE_TO_EV = 27.211386245988
HARTREE_TO_CM = 219474.6313632
# atomic mass of 1-H in electron masses (1.00782503 u x 1822.888486 me/u)
MASS_H = 1837.4713
REDUCED_MASS_H2 = MASS_H / 2.0

# experimental reference values for H2
EXP_R_E = 0.7414      # Angstrom
EXP_D_E = 4.7466      # eV
EXP_OMEGA = 4401.2    # cm^-1


def fit_minimum(r, e, window=2):
    """Locate the minimum by fitting a parabola, not by reading off the grid.

    `window` is the number of points either side of the lowest sampled
    point. SMALLER IS BETTER for the curvature: a real potential is
    anharmonic, so a wide window fits the anharmonicity as if it were
    curvature and inflates the frequency. Use frequency_convergence() to
    check you are in the converged regime.

    Returns (r_equilibrium_angstrom, e_minimum_hartree, quadratic_coeffs).
    """
    i = int(np.argmin(e))
    lo = max(0, i - window)
    hi = min(len(r), i + window + 1)

    coeffs = np.polyfit(r[lo:hi], e[lo:hi], 2)
    r_eq = -coeffs[1] / (2 * coeffs[0])
    e_min = np.polyval(coeffs, r_eq)
    return r_eq, e_min, coeffs


def dissociation_limit(basis="sto-3g"):
    """Energy of two infinitely separated H atoms, computed analytically.

    Do NOT use the last point of your scan as the asymptote. At 2.5 A the
    H2 curve is still bound by about 2.9 mHa, so the last grid point
    UNDERESTIMATES the well depth.
    """
    mol = gto.M(atom="H 0 0 0", basis=basis, spin=1, verbose=0)
    e_h = scf.UHF(mol).run(verbose=0).e_tot
    return 2.0 * e_h


def well_depth(e_min, e_asymptote):
    """Dissociation energy D_e in Hartree and eV."""
    d_e = e_asymptote - e_min
    return d_e, d_e * HARTREE_TO_EV


def harmonic_frequency(coeffs):
    """Vibrational frequency from the curvature at the minimum.

    The parabola was fitted in Angstrom, so the second derivative must be
    converted to Hartree per Bohr squared before combining with the reduced
    mass in atomic units.
    """
    d2E_dR2_angstrom = 2.0 * coeffs[0]                       # Ha / A^2
    k = d2E_dR2_angstrom / (BOHR_PER_ANGSTROM ** 2)          # Ha / Bohr^2

    omega_au = np.sqrt(k / REDUCED_MASS_H2)                  # atomic units
    return omega_au * HARTREE_TO_CM                          # cm^-1


def frequency_convergence(r, e, windows=(2, 3, 4, 5, 6, 8)):
    """Show how the extracted observables drift with the fit window.

    A converged answer is one that stops changing as the window shrinks.
    If your numbers are still moving at the narrowest window, your grid is
    too coarse near the minimum.
    """
    print(f"  {'window':>7} {'span/A':>8} {'R_e/A':>9} {'omega/cm-1':>11}")
    for w in windows:
        i = int(np.argmin(e))
        lo, hi = max(0, i - w), min(len(r), i + w + 1)
        if hi - lo < 3:
            continue
        _, _, co = fit_minimum(r, e, window=w)
        r_eq = -co[1] / (2 * co[0])
        print(f"  {w:>7} {r[hi-1]-r[lo]:8.3f} {r_eq:9.4f} "
              f"{harmonic_frequency(co):11.1f}")


def analyse(path="data/scan.npz", window=2):
    d = np.load(path)
    r, e_hf, e_fci, e_vqe = d["grid"], d["e_hf"], d["e_fci"], d["e_vqe"]

    r_eq, e_min, coeffs = fit_minimum(r, e_vqe, window=window)
    e_inf = dissociation_limit()
    d_e_ha, d_e_ev = well_depth(e_min, e_inf)
    omega = harmonic_frequency(coeffs)

    print("Extracted from the VQE curve")
    print("=" * 60)
    print(f"  equilibrium bond length   {r_eq:10.4f} A     "
          f"(exp {EXP_R_E:.4f}, {100*(r_eq-EXP_R_E)/EXP_R_E:+.2f} %)")
    print(f"      lowest grid point     {r[np.argmin(e_vqe)]:10.4f} A")
    print(f"  minimum energy            {e_min:10.6f} Ha")
    print(f"  dissociation limit 2E(H)  {e_inf:10.6f} Ha")
    print(f"      last grid point       {e_vqe[-1]:10.6f} Ha  "
          f"(still bound by {(e_vqe[-1]-e_inf)*1000:.2f} mHa)")
    print(f"  well depth D_e            {d_e_ev:10.4f} eV    "
          f"(exp {EXP_D_E:.4f}, {100*(d_e_ev-EXP_D_E)/EXP_D_E:+.1f} %)")
    print(f"  harmonic frequency        {omega:10.1f} cm-1  "
          f"(exp {EXP_OMEGA:.1f}, {100*(omega-EXP_OMEGA)/EXP_OMEGA:+.1f} %)")
    print()
    print(f"  max |VQE - FCI|           "
          f"{np.abs(e_vqe-e_fci).max()*1000:10.6f} mHa")
    print(f"  correlation energy at R_e "
          f"{(e_hf[np.argmin(e_vqe)]-e_min)*1000:10.4f} mHa")
    print()
    print("Fit-window sensitivity (anharmonicity check)")
    print("=" * 60)
    frequency_convergence(r, e_vqe)

    return dict(r_eq=r_eq, e_min=e_min, d_e_ev=d_e_ev, omega=omega)


def plot(path="data/scan.npz",
         out="results/figures/dissociation_curve.png", window=2):
    d = np.load(path)
    r, e_hf, e_fci, e_vqe = d["grid"], d["e_hf"], d["e_fci"], d["e_vqe"]
    r_eq, e_min, _ = fit_minimum(r, e_vqe, window=window)
    e_inf = dissociation_limit()

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(r, e_hf, "-", color="#b03a3a", lw=2, label="Hartree-Fock")
    ax.plot(r, e_fci, "-", color="#1a4d7a", lw=2.5, label="FCI (exact)")
    ax.plot(r, e_vqe, "o", color="#c0632a", ms=4.5, mfc="none", mew=1.3,
            label="VQE (UCCSD)")
    ax.axhline(e_inf, color="grey", ls=":", lw=1.2)
    ax.text(2.45, e_inf + 0.008, "2 x E(H)", fontsize=8, color="grey",
            ha="right")
    ax.plot([r_eq], [e_min], "*", color="#1a4d7a", ms=15, zorder=5)
    ax.annotate("", xy=(2.1, e_min), xytext=(2.1, e_inf),
                arrowprops=dict(arrowstyle="<|-|>", color="#2e7d4f", lw=1.4))
    ax.text(2.15, (e_min + e_inf) / 2, "$D_e$", color="#2e7d4f", fontsize=10,
            va="center")

    ax.set_xlabel("H-H internuclear distance (Angstrom)")
    ax.set_ylabel("total energy (Hartree)")
    ax.set_title("H$_2$ dissociation curve, STO-3G")
    ax.legend(frameon=False, loc="lower right")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=200)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    analyse()
    plot()
