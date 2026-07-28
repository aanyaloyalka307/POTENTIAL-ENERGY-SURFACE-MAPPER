"""landscape.py - the optimisation landscape E(R, theta) as a 3D surface.

The dissociation curve is energy against ONE variable, so it is a curve and
nothing is gained by drawing it in three dimensions. There is, however, a
genuine surface in this problem: the energy as a function of both the
geometry R and the ansatz parameter theta.

That surface is worth plotting because it explains the Phase 6 result. The
valley floor - the optimal theta at each geometry - moves smoothly as the
bond stretches. Continuation follows that valley and always lands in it.
A random start at a stretched geometry does not know where the valley is.
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pennylane as qml
from matplotlib import cm

from hamiltonian import ELECTRONS, qubit_hamiltonian

OUT_DATA = "data/landscape.npz"
OUT_FIG = "results/figures/optimisation_landscape.png"


def compute(r_min=0.30, r_max=2.50, r_step=0.05, n_theta=121):
    """Evaluate <psi(theta)|H(R)|psi(theta)> on a grid of (R, theta).

    Only the double-excitation parameter is swept; the two single
    excitations vanish by symmetry for H2 (see Phase 3), so they are held
    at zero and the landscape is genuinely two-dimensional.
    """
    R = np.round(np.arange(r_min, r_max + 1e-9, r_step), 4)
    TH = np.linspace(-np.pi, np.pi, n_theta)

    singles, doubles = qml.qchem.excitations(ELECTRONS, 4)
    s_wires, d_wires = qml.qchem.excitations_to_wires(singles, doubles)
    hf = qml.qchem.hf_state(ELECTRONS, 4)
    dev = qml.device("default.qubit", wires=4)

    @qml.qnode(dev)
    def energy(params, H):
        qml.UCCSD(params, wires=range(4), s_wires=s_wires, d_wires=d_wires,
                  init_state=hf)
        return qml.expval(H)

    Z = np.zeros((len(TH), len(R)))
    for j, r in enumerate(R):
        H, _ = qubit_hamiltonian(float(r))
        for i, th in enumerate(TH):
            Z[i, j] = energy(np.array([0.0, 0.0, th]), H)

    os.makedirs(os.path.dirname(OUT_DATA), exist_ok=True)
    np.savez(OUT_DATA, R=R, TH=TH, Z=Z)
    return R, TH, Z


def plot(path=OUT_DATA, out=OUT_FIG):
    d = np.load(path)
    R, TH, Z = d["R"], d["TH"], d["Z"]
    theta_star = TH[Z.argmin(axis=0)]
    e_star = Z.min(axis=0)

    # The repulsive wall at short R is an order of magnitude taller than the
    # valley, so it swamps both the colour scale and the z axis. Cap the
    # display range; the wall is physics, not the subject of this figure.
    ZTOP = 0.4
    Zc = np.minimum(Z, ZTOP)

    fig = plt.figure(figsize=(12, 5.2))

    # --- 3D surface -----------------------------------------------------
    ax = fig.add_subplot(1, 2, 1, projection="3d")
    RR, TT = np.meshgrid(R, TH)
    ax.plot_surface(RR, TT, Zc, cmap=cm.viridis, alpha=0.88, linewidth=0,
                    antialiased=True, rstride=2, cstride=1,
                    vmin=Z.min(), vmax=ZTOP)
    ax.plot(R, theta_star, e_star, color="#c0632a", lw=3, zorder=10,
            label=r"valley floor $\theta^*(R)$")
    ax.set_xlabel("bond length R (Å)", fontsize=9, labelpad=6)
    ax.set_ylabel(r"ansatz parameter $\theta$ (rad)", fontsize=9, labelpad=6)
    ax.set_zlabel("energy (Ha)", fontsize=9, labelpad=4)
    ax.set_zlim(Z.min() - 0.05, ZTOP)
    ax.set_title("The surface VQE is searching\n"
                 r"(orange: the valley floor $\theta^*(R)$)",
                 fontsize=10.5, weight="bold", pad=6, linespacing=1.5)
    ax.view_init(elev=26, azim=-56)

    # --- contour view with the path -------------------------------------
    ax2 = fig.add_subplot(1, 2, 2)
    cs = ax2.contourf(R, TH, Zc, levels=np.linspace(Z.min(), ZTOP, 40),
                      cmap="viridis", extend="max")
    ax2.set_xlim(R[0], R[-1] + 0.06)
    ax2.plot(R, theta_star, color="#c0632a", lw=2.6,
             label=r"valley floor $\theta^*(R)$")
    ax2.scatter([R[0]], [theta_star[0]], s=70, color="white",
                edgecolor="#c0632a", zorder=6, lw=1.8)
    ax2.annotate("continuation starts here\nand follows the valley",
                 xy=(R[0], theta_star[0]), xytext=(0.55, -1.55),
                 fontsize=8.2, color="white", weight="bold", linespacing=1.35,
                 arrowprops=dict(arrowstyle="-|>", color="white", lw=1.3))
    ax2.axvline(2.5, color="#ff6f61", ls="--", lw=1.8)
    ax2.annotate("a random start at 2.5 Å\nlands anywhere on this line",
                 xy=(2.5, -2.2), xytext=(1.28, -2.80), fontsize=8.2,
                 color="#ffd9d5", weight="bold", linespacing=1.35,
                 arrowprops=dict(arrowstyle="-|>", color="#ff6f61", lw=1.4))
    ax2.set_xlabel("bond length R (Å)", fontsize=9.5)
    ax2.set_ylabel(r"ansatz parameter $\theta$ (rad)", fontsize=9.5)
    ax2.set_title("Why continuation works and random starts do not",
                  fontsize=10.5, weight="bold")
    ax2.legend(fontsize=8.5, frameon=False, loc="upper left",
               labelcolor="white")
    cb = fig.colorbar(cs, ax=ax2, label="energy (Ha)", pad=0.02,
                      ticks=np.arange(-1.0, ZTOP + 0.01, 0.25))
    cb.ax.tick_params(labelsize=8)

    fig.tight_layout()
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=200)
    print(f"wrote {out}")

    print(f"\n  theta* at R=0.30 A : {theta_star[0]:+.4f} rad")
    print(f"  theta* at R=2.50 A : {theta_star[-1]:+.4f} rad")
    print(f"  the valley floor moves by "
          f"{abs(theta_star[-1]-theta_star[0]):.3f} rad across the scan")


if __name__ == "__main__":
    if not os.path.exists(OUT_DATA):
        print("computing the landscape (about 25 s)...")
        compute()
    plot()
