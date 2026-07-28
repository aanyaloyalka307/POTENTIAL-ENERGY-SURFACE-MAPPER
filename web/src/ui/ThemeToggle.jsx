import React from "react";
import { motion, AnimatePresence } from "framer-motion";

function SunIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="4.2" stroke="currentColor" strokeWidth="1.7" />
      {Array.from({ length: 8 }).map((_, i) => {
        const a = (i * Math.PI) / 4;
        const x1 = 12 + Math.cos(a) * 7.4;
        const y1 = 12 + Math.sin(a) * 7.4;
        const x2 = 12 + Math.cos(a) * 9.4;
        const y2 = 12 + Math.sin(a) * 9.4;
        return (
          <line
            key={i}
            x1={x1}
            y1={y1}
            x2={x2}
            y2={y2}
            stroke="currentColor"
            strokeWidth="1.7"
            strokeLinecap="round"
          />
        );
      })}
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M20 14.2A8 8 0 1 1 9.8 4 6.4 6.4 0 0 0 20 14.2Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function ThemeToggle({ theme, onToggle }) {
  const isDark = theme === "dark";
  return (
    <motion.button
      type="button"
      className="theme-toggle"
      onClick={onToggle}
      whileTap={{ scale: 0.92 }}
      aria-pressed={!isDark}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      title={isDark ? "Light mode" : "Dark mode"}
    >
      <AnimatePresence mode="wait" initial={false}>
        <motion.span
          key={theme}
          className="tt-icon"
          initial={{ rotate: -35, opacity: 0, scale: 0.7 }}
          animate={{ rotate: 0, opacity: 1, scale: 1 }}
          exit={{ rotate: 35, opacity: 0, scale: 0.7 }}
          transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
        >
          {isDark ? <SunIcon /> : <MoonIcon />}
        </motion.span>
      </AnimatePresence>
      <span className="tt-label mono">{isDark ? "Light" : "Dark"}</span>
    </motion.button>
  );
}
