import React, { useCallback, useEffect, useState } from "react";
import { useReducedMotion } from "framer-motion";
import Scene from "./Scene.jsx";
import Dock from "./ui/Dock.jsx";
import Readout from "./ui/Readout.jsx";
import ThemeToggle from "./ui/ThemeToggle.jsx";
import { nR, meta, valleyReadout, randomReadout } from "./lib/surface.js";
import { PALETTE, getInitialTheme } from "./lib/theme.js";

export default function App() {
  const reduce = useReducedMotion();
  const [theme, setTheme] = useState(getInitialTheme);
  const [jIndex, setJIndex] = useState(0);
  const [mode, setMode] = useState("idle"); // idle | continuation | random
  const [randomI, setRandomI] = useState(null);
  const [wireframe, setWireframe] = useState(false);
  const [resetToken, setResetToken] = useState(0);

  // Reflect the theme onto <html data-theme> (drives the CSS variables) and
  // remember the choice.
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("pes-theme", theme);
    } catch (e) {
      /* file:// may block storage; the toggle still works for the session */
    }
  }, [theme]);
  const toggleTheme = useCallback(
    () => setTheme((t) => (t === "dark" ? "light" : "dark")),
    []
  );

  // Continuation: step along the valley floor from short bond to dissociation.
  useEffect(() => {
    if (mode !== "continuation") return undefined;
    if (reduce) {
      setJIndex(nR - 1);
      setMode("idle");
      return undefined;
    }
    let raf;
    let acc = 0;
    let prev = performance.now();
    const tick = (now) => {
      acc += now - prev;
      prev = now;
      if (acc >= 45) {
        acc = 0;
        setJIndex((j) => {
          if (j >= nR - 1) {
            setMode("idle");
            return j;
          }
          return j + 1;
        });
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [mode, reduce]);

  const handleContinuation = useCallback(() => {
    setMode((m) => {
      if (m === "continuation") return "idle";
      setRandomI(null);
      setJIndex(0);
      return "continuation";
    });
  }, []);

  const handleRandom = useCallback(() => {
    setMode("idle");
    // a blind guess: any theta index at the far, stretched geometry
    setRandomI(Math.floor(Math.random() * meta.nTheta));
    setMode("random");
  }, []);

  const handleScrub = useCallback((j) => {
    setMode("idle");
    setRandomI(null);
    setJIndex(j);
  }, []);

  const pal = PALETTE[theme];
  const readout =
    mode === "random" && randomI != null ? randomReadout(randomI) : valleyReadout(jIndex);
  const markerColor = readout.onValley ? pal.teal : pal.amber;

  return (
    <div className="stage">
      <Scene
        theme={theme}
        wireframe={wireframe}
        markerTarget={readout.world}
        markerColor={markerColor}
        resetToken={resetToken}
      />
      <div className="grain" />

      <header className="topbar">
        <div className="brand">
          Potential&nbsp;Energy&nbsp;<em>Surface</em>
          <span className="sub">H₂ · VQE optimisation landscape E(R, θ)</span>
        </div>
        <div className="topbar-right">
          <ThemeToggle theme={theme} onToggle={toggleTheme} />
          <div className="creditline">
            {meta.nR}×{meta.nTheta} grid
            <br />
            θ* drift {meta.thetaDrift} rad
          </div>
        </div>
      </header>

      <Readout data={readout} />

      <Dock
        jIndex={jIndex}
        onScrub={handleScrub}
        mode={mode}
        onContinuation={handleContinuation}
        onRandom={handleRandom}
        wireframe={wireframe}
        onWireframe={() => setWireframe((w) => !w)}
        onReset={() => setResetToken((t) => t + 1)}
      />
    </div>
  );
}
