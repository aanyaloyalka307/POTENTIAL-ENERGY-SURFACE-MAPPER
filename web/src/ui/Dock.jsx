import React from "react";
import { motion } from "framer-motion";
import { D, nR } from "../lib/surface.js";

const tap = { scale: 0.96 };

export default function Dock({
  jIndex,
  onScrub,
  mode,
  onContinuation,
  onRandom,
  wireframe,
  onWireframe,
  onReset,
}) {
  const r = D.R[jIndex];
  const pct = (jIndex / (nR - 1)) * 100;
  const playing = mode === "continuation";

  return (
    <motion.section
      className="panel dock"
      initial={{ opacity: 0, y: 26 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1], delay: 0.1 }}
    >
      <div className="scrub">
        <span className="cap mono">
          R&nbsp;<b>{r.toFixed(3)} Å</b>
        </span>
        <input
          className="slider mono"
          type="range"
          min={0}
          max={nR - 1}
          step={1}
          value={jIndex}
          onChange={(e) => onScrub(Number(e.target.value))}
          style={{ "--pct": `${pct}%` }}
          aria-label="Bond length index"
        />
        <span className="cap mono" style={{ color: "var(--ink-faint)" }}>
          {jIndex + 1}/{nR}
        </span>
      </div>

      <div className="buttons">
        <motion.button
          className={`btn primary ${playing ? "active" : ""}`}
          whileTap={tap}
          onClick={onContinuation}
        >
          <span className="dot" />
          {playing ? "Stop" : "Continuation"}
        </motion.button>

        <motion.button className="btn warm" whileTap={tap} onClick={onRandom}>
          <span className="dot" />
          Random start
        </motion.button>

        <motion.button
          className="btn"
          whileTap={tap}
          onClick={onWireframe}
          aria-pressed={wireframe}
        >
          Wireframe
        </motion.button>

        <motion.button className="btn" whileTap={tap} onClick={onReset}>
          Reset view
        </motion.button>
      </div>
    </motion.section>
  );
}
