import React from "react";
import { motion } from "framer-motion";
import { CHEM_ACC_MHA } from "../lib/surface.js";

function Val({ children, unit }) {
  return (
    <span className="v mono">
      {children}
      {unit && <span className="u">{unit}</span>}
    </span>
  );
}

export default function Readout({ data }) {
  const { r, theta, e, delta, onValley } = data;

  let verdict = null;
  if (delta != null) {
    if (onValley) {
      verdict = {
        color: "var(--good)",
        text: `ON THE VALLEY FLOOR\n${delta.toFixed(3)} mHa from exact`,
      };
    } else if (Math.abs(delta) > CHEM_ACC_MHA) {
      verdict = {
        color: "var(--miss)",
        text: `RANDOM START\nmisses by ${delta.toFixed(1)} mHa`,
      };
    } else {
      verdict = { color: "var(--good)", text: "RANDOM START\nlucky hit" };
    }
  }

  return (
    <motion.aside
      className="panel readout"
      initial={{ opacity: 0, x: 24 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1], delay: 0.15 }}
      aria-live="polite"
    >
      <div className="panel-label">Readout</div>
      <div className="rows">
        <div className="row">
          <span className="k">bond length R</span>
          <Val unit="Å">{r.toFixed(3)}</Val>
        </div>
        <div className="row">
          <span className="k">parameter θ</span>
          <Val unit="rad">{theta >= 0 ? `+${theta.toFixed(4)}` : theta.toFixed(4)}</Val>
        </div>
        <div className="row">
          <span className="k">energy</span>
          <Val unit="Ha">{e.toFixed(6)}</Val>
        </div>
        <div className="row">
          <span className="k">vs exact</span>
          <Val unit="mHa">
            {delta == null ? "—" : `${delta >= 0 ? "+" : ""}${delta.toFixed(3)}`}
          </Val>
        </div>
      </div>

      {verdict && (
        <div className="verdict" style={{ color: verdict.color, whiteSpace: "pre-line" }}>
          {verdict.text}
        </div>
      )}

      <p className="hint">
        Drag to orbit · scroll to zoom. Continuation rides the valley out to full
        dissociation; a random start is a blind guess with no reason to land near θ*.
      </p>
    </motion.aside>
  );
}
