"""viewer.py - the optimisation landscape E(R, theta), interactively.

The static figure from landscape.py makes the argument, but it fixes one
viewpoint and one moment in time. This opens the same surface in a window you
can orbit, and animates the two things the figure can only assert:

    Continuation   walks the valley floor from 0.30 A out to full
                   dissociation, staying within a fraction of a mHa of exact
                   the whole way.
    Random start   drops a blind guess at 2.50 A and reports how far it lands
                   from the FCI reference. Usually a long way.

Run it after the grid exists:

    python landscape.py     # writes data/landscape.npz (~25 s)
    python viewer.py
"""

import os
import sys

import numpy as np

import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize
from matplotlib.widgets import Button, Slider

DATA = "data/landscape.npz"
SCAN = "data/scan.npz"

# The repulsive wall at short R is an order of magnitude taller than the
# valley. Clipping it flat renders as a fake tabletop, so compress it with a
# log above the knee: the wall keeps rising and still reads as a wall, without
# swamping the feature the plot is actually about.
ZTOP = 0.40
KNEE = 0.30
ZMAX = 2.65

# Above this, a random start counts as having missed the valley rather than
# having got lucky. Chemical accuracy is 1.6 mHa.
MISS_MHA = 1.6

VALLEY = "#c0632a"
WALKER = "#ffce7a"
RANDOM = "#e8574a"


def squash(e):
    """Compress energies above the knee so the wall does not dominate.

    Written branchlessly: `over` is clamped at zero, so log1p never sees an
    argument below -1 and the below-knee case costs nothing.
    """
    e = np.asarray(e, dtype=float)
    over = np.maximum(e - ZTOP, 0.0)
    return np.minimum(e, ZTOP) + KNEE * np.log1p(over / KNEE)


def load():
    if not os.path.exists(DATA):
        sys.exit(f"{DATA} not found - run `python landscape.py` first (~25 s).")
    d = np.load(DATA)
    R, TH, Z = d["R"], d["TH"], d["Z"]

    fci = {}
    if os.path.exists(SCAN):
        s = np.load(SCAN)
        for r, e in zip(s["grid"], s["e_fci"]):
            fci[round(float(r), 2)] = float(e)
    return R, TH, Z, fci


class Viewer:
    def __init__(self):
        self.R, self.TH, self.Z, self.fci = load()
        self.nr = len(self.R)
        self.theta_idx = self.Z.argmin(axis=0)      # valley floor, per geometry
        self.theta_star = self.TH[self.theta_idx]
        self.e_star = self.Z.min(axis=0)

        self.zmin = float(self.Z.min())
        self.wire = False
        self.surface = None
        self.timer = None

        self._build_figure()
        self._draw_surface()
        self._draw_valley()
        self.home = (self.ax.elev, self.ax.azim, self._limits())
        self.set_walker(0)

    # ---- figure scaffolding ------------------------------------------------
    def _build_figure(self):
        self.fig = plt.figure(figsize=(12.5, 7.6))
        self.fig.canvas.manager.set_window_title(
            "H2 optimisation landscape - E(R, theta)")

        self.ax = self.fig.add_axes([0.02, 0.25, 0.66, 0.64], projection="3d")
        self.ax.set_xlabel("bond length R (Å)", fontsize=9, labelpad=8)
        self.ax.set_ylabel(r"ansatz parameter $\theta$ (rad)", fontsize=9,
                           labelpad=8)
        self.ax.set_zlabel("energy (Ha)", fontsize=9, labelpad=6)
        self.ax.view_init(elev=26, azim=-56)
        self.ax.set_title("The surface VQE is searching\n"
                          r"(orange: the valley floor $\theta^*(R)$)",
                          fontsize=11, weight="bold", linespacing=1.5)

        self._build_readout()
        self._build_controls()
        self.fig.canvas.mpl_connect("scroll_event", self.on_scroll)

    def _build_readout(self):
        """The numeric panel down the right-hand side."""
        x = 0.72
        self.fig.text(x, 0.90, "READOUT", fontsize=9.5, weight="bold",
                      family="monospace", color="#444")
        rows = [("R", "bond length"), ("t", r"$\theta$"),
                ("e", "energy"), ("d", "vs exact")]
        self.out = {}
        for k, (key, label) in enumerate(rows):
            y = 0.845 - k * 0.052
            self.fig.text(x, y, label, fontsize=9, color="#666")
            self.out[key] = self.fig.text(x + 0.14, y, "—", fontsize=10.5,
                                          family="monospace", weight="bold")
        self.verdict = self.fig.text(x, 0.60, "", fontsize=9.5,
                                     family="monospace", weight="bold",
                                     wrap=True)

        self.fig.text(x, 0.40,
                      "Continuation enters the valley where the\n"
                      "problem is easy and rides it out to full\n"
                      "dissociation. A random start at 2.50 Å is a\n"
                      "blind guess along the dashed red line, with\n"
                      "no reason to land anywhere near θ*.",
                      fontsize=8.2, color="#555", linespacing=1.6)
        self.fig.text(x, 0.30, "drag to orbit · scroll to zoom",
                      fontsize=8, color="#999", style="italic")

    def _build_controls(self):
        self.s_ax = self.fig.add_axes([0.08, 0.15, 0.54, 0.03])
        self.slider = Slider(self.s_ax, "R index", 0, self.nr - 1,
                             valinit=0, valstep=1, color="#8a6224")
        self.slider.on_changed(self.on_slide)

        specs = [("play", "▶ Continuation", 0.08, self.on_play),
                 ("rand", "Random start", 0.22, self.on_random),
                 ("wire", "Wireframe", 0.36, self.on_wire),
                 ("reset", "Reset view", 0.50, self.on_reset)]
        self.buttons = {}
        for name, text, x, cb in specs:
            a = self.fig.add_axes([x, 0.05, 0.12, 0.055])
            b = Button(a, text, color="#eeeeee", hovercolor="#dddddd")
            b.label.set_fontsize(9.5)
            b.on_clicked(cb)
            self.buttons[name] = b
        self.buttons["rand"].label.set_color(RANDOM)

    # ---- geometry ----------------------------------------------------------
    def _limits(self):
        return (self.ax.get_xlim(), self.ax.get_ylim(), self.ax.get_zlim())

    def _draw_surface(self):
        """(Re)draw the surface mesh. Called again when wireframe toggles."""
        if self.surface is not None:
            self.surface.remove()

        RR, TT = np.meshgrid(self.R, self.TH)
        ZS = squash(self.Z)

        if self.wire:
            self.surface = self.ax.plot_wireframe(
                RR, TT, ZS, rstride=3, cstride=2, linewidth=0.4,
                color="#2a6f8a", alpha=0.75)
        else:
            norm = Normalize(vmin=self.zmin, vmax=ZTOP)
            colors = cm.viridis(norm(np.minimum(self.Z, ZTOP)))
            self.surface = self.ax.plot_surface(
                RR, TT, ZS, facecolors=colors, rstride=2, cstride=1,
                linewidth=0, antialiased=True, shade=False, alpha=0.92)

        self.ax.set_zlim(self.zmin - 0.05, squash(ZMAX))

    def _draw_valley(self):
        self.ax.plot(self.R, self.theta_star, squash(self.e_star) + 0.01,
                     color=VALLEY, lw=2.8, zorder=10)

        # the vertical line a random start at 2.50 A lands somewhere along
        self.ax.plot([self.R[-1]] * 2, [self.TH[0], self.TH[-1]],
                     [self.zmin - 0.04] * 2, color=RANDOM, ls="--", lw=1.6)

        self.walker, = self.ax.plot([], [], [], "o", color=WALKER,
                                    markersize=9, markeredgecolor="#8a5a10",
                                    zorder=12)
        self.rnd, = self.ax.plot([], [], [], "o", color=RANDOM, markersize=8.5,
                                 markeredgecolor="#7a1f16", zorder=12)
        self.rnd.set_visible(False)

    # ---- state -------------------------------------------------------------
    def show(self, j, i, is_random):
        r, th, e = self.R[j], self.TH[i], self.Z[i][j]
        self.out["R"].set_text(f"{r:.3f} Å")
        self.out["t"].set_text(f"{th:+.4f} rad")
        self.out["e"].set_text(f"{e:.6f} Ha")

        ref = self.fci.get(round(float(r), 2))
        if ref is None:
            self.out["d"].set_text("—")
            self.verdict.set_text("")
            return

        d = (e - ref) * 1000.0
        self.out["d"].set_text(f"{d:+.3f} mHa")
        if is_random:
            if d > MISS_MHA:
                self.verdict.set_text(f"random start\nmisses by {d:.1f} mHa")
                self.verdict.set_color(RANDOM)
            else:
                self.verdict.set_text("random start\nlucky hit")
                self.verdict.set_color("#2e8b57")
        else:
            self.verdict.set_text(f"on the valley floor\n{d:.3f} mHa from exact")
            self.verdict.set_color("#2e8b57")

    def set_walker(self, j):
        j = int(j)
        i = int(self.theta_idx[j])
        self.walker.set_data_3d([self.R[j]], [self.theta_star[j]],
                                [squash(self.e_star[j]) + 0.04])
        self.rnd.set_visible(False)
        self.show(j, i, False)

        # Keep the handle under the walker however the walker got there, but
        # suppress the callback so this does not re-enter through on_slide.
        if int(self.slider.val) != j:
            self.slider.eventson = False
            self.slider.set_val(j)
            self.slider.eventson = True

        self.fig.canvas.draw_idle()

    # ---- callbacks ---------------------------------------------------------
    def stop(self):
        if self.timer is not None:
            self.timer.stop()
            self.timer = None
            self.buttons["play"].label.set_text("▶ Continuation")
            self.fig.canvas.draw_idle()

    def on_slide(self, val):
        self.stop()
        self.set_walker(val)

    def on_play(self, _event):
        if self.timer is not None:
            self.stop()
            return
        self.buttons["play"].label.set_text("■ Stop")
        self._j = 0

        def step():
            if self._j >= self.nr:
                self.stop()
                return
            self.set_walker(self._j)            # syncs the slider itself
            self._j += 1

        self.timer = self.fig.canvas.new_timer(interval=55)
        self.timer.add_callback(step)
        self.timer.start()

    def on_random(self, _event):
        self.stop()
        j = self.nr - 1
        i = int(np.random.randint(len(self.TH)))
        self.rnd.set_data_3d([self.R[j]], [self.TH[i]],
                             [squash(self.Z[i][j]) + 0.04])
        self.rnd.set_visible(True)
        self.show(j, i, True)
        self.fig.canvas.draw_idle()

    def on_wire(self, _event):
        self.wire = not self.wire
        self._draw_surface()
        self.fig.canvas.draw_idle()

    def on_reset(self, _event):
        elev, azim, (xl, yl, zl) = self.home
        self.ax.view_init(elev=elev, azim=azim)
        self.ax.set_xlim(xl)
        self.ax.set_ylim(yl)
        self.ax.set_zlim(zl)
        self.fig.canvas.draw_idle()

    def on_scroll(self, event):
        """Scroll to zoom, by shrinking the axis limits about their centre."""
        if event.inaxes is not self.ax:
            return
        f = 0.9 if event.button == "up" else 1 / 0.9
        for get, set_ in ((self.ax.get_xlim, self.ax.set_xlim),
                          (self.ax.get_ylim, self.ax.set_ylim),
                          (self.ax.get_zlim, self.ax.set_zlim)):
            lo, hi = get()
            mid, half = (lo + hi) / 2, (hi - lo) / 2 * f
            set_(mid - half, mid + half)
        self.fig.canvas.draw_idle()


def main():
    v = Viewer()
    print(f"  grid: {v.nr} geometries x {len(v.TH)} theta")
    print(f"  theta* moves {abs(v.theta_star[-1] - v.theta_star[0]):.3f} rad "
          f"across the scan")
    plt.show()
    return v


if __name__ == "__main__":
    main()
