// Theme palettes for the 3D scene (the DOM/UI side is driven by CSS variables
// under :root[data-theme=...]; these are the values Three.js needs directly:
// clear colour, fog, grid, lights, and accents that must stay legible against
// each background).
export const PALETTE = {
  dark: {
    teal: "#38e1c4",
    amber: "#ffb454",
    bg: "#0b0e11",
    grid: ["#1e2a31", "#161f25"],
    fog: [20, 42],
    ambient: 0.55,
    key: 1.15,
    keyColor: "#eaf4ff",
    rim: 0.4,
    rimColor: "#38e1c4",
  },
  light: {
    teal: "#0e9e8a",
    amber: "#c9761f",
    bg: "#e9ecee",
    grid: ["#b9c2c7", "#ccd4d8"],
    fog: [24, 50],
    ambient: 0.9,
    key: 1.05,
    keyColor: "#ffffff",
    rim: 0.22,
    rimColor: "#0e9e8a",
  },
};

export function getInitialTheme() {
  try {
    const saved = localStorage.getItem("pes-theme");
    if (saved === "light" || saved === "dark") return saved;
  } catch (e) {
    /* localStorage may be unavailable on file:// — fall through */
  }
  if (
    typeof matchMedia !== "undefined" &&
    matchMedia("(prefers-color-scheme: light)").matches
  ) {
    return "light";
  }
  return "dark";
}
