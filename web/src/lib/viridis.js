// A compact viridis colormap. Same perceptually-uniform map matplotlib uses
// for the desktop figures, so the web surface reads as the same object. 16
// stops sampled from the reference map; we lerp between them.
const STOPS = [
  [0.267, 0.005, 0.329],
  [0.283, 0.131, 0.449],
  [0.262, 0.242, 0.521],
  [0.221, 0.336, 0.548],
  [0.185, 0.418, 0.556],
  [0.154, 0.498, 0.558],
  [0.128, 0.567, 0.551],
  [0.122, 0.633, 0.531],
  [0.166, 0.699, 0.497],
  [0.278, 0.763, 0.446],
  [0.42, 0.803, 0.377],
  [0.588, 0.835, 0.288],
  [0.741, 0.873, 0.15],
  [0.876, 0.891, 0.096],
  [0.964, 0.902, 0.136],
  [0.993, 0.906, 0.144],
];

// Returns [r, g, b] in 0..1 for t in 0..1.
export function viridis(t) {
  t = t < 0 ? 0 : t > 1 ? 1 : t;
  const x = t * (STOPS.length - 1);
  const i = Math.floor(x);
  const f = x - i;
  const a = STOPS[i];
  const b = STOPS[Math.min(i + 1, STOPS.length - 1)];
  return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f];
}
