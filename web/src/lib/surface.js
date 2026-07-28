// Turns the baked landscape.json into everything the 3D scene needs: a mapping
// from physical (R, theta, energy) into a comfortable world box, the surface
// buffer geometry with viridis vertex colours, and the valley-floor polyline.
import data from "../data/landscape.json";
import { viridis } from "./viridis.js";

export const D = data;

const { R, TH, Z, valley, fciOnR, meta } = data;
export const nR = meta.nR;
export const nTheta = meta.nTheta;

// display compression of the repulsive wall — matches viewer.squash()
const ZTOP = meta.zTop;
const KNEE = 0.3;
export function squash(e) {
  const over = Math.max(e - ZTOP, 0);
  return Math.min(e, ZTOP) + KNEE * Math.log1p(over / KNEE);
}

// world box
export const WIDTH = 12; // along R (x)
export const DEPTH = 9; // along theta (z)
export const HEIGHT = 3.7; // energy (y)

let zMax = -Infinity;
for (const row of Z) for (const v of row) if (v > zMax) zMax = v;
const sMin = squash(meta.zMin);
const sMax = squash(zMax);

export const X = (r) => ((r - meta.rMin) / (meta.rMax - meta.rMin)) * WIDTH - WIDTH / 2;
export const ZC = (t) =>
  ((t - meta.thetaMin) / (meta.thetaMax - meta.thetaMin)) * DEPTH - DEPTH / 2;
export const Y = (e) => ((squash(e) - sMin) / (sMax - sMin)) * HEIGHT;

// colour by raw energy, clamped at the wall knee so the valley keeps contrast
function colorFor(e) {
  const t = (Math.min(e, ZTOP) - meta.zMin) / (ZTOP - meta.zMin);
  return viridis(t);
}

// Build flat arrays for a BufferGeometry: rows = theta (i), cols = R (j).
export function buildSurfaceArrays() {
  const positions = new Float32Array(nTheta * nR * 3);
  const colors = new Float32Array(nTheta * nR * 3);
  for (let i = 0; i < nTheta; i++) {
    for (let j = 0; j < nR; j++) {
      const k = (i * nR + j) * 3;
      const e = Z[i][j];
      positions[k] = X(R[j]);
      positions[k + 1] = Y(e);
      positions[k + 2] = ZC(TH[i]);
      const c = colorFor(e);
      colors[k] = c[0];
      colors[k + 1] = c[1];
      colors[k + 2] = c[2];
    }
  }
  const indices = new Uint32Array((nTheta - 1) * (nR - 1) * 6);
  let p = 0;
  for (let i = 0; i < nTheta - 1; i++) {
    for (let j = 0; j < nR - 1; j++) {
      const a = i * nR + j;
      const b = i * nR + j + 1;
      const c = (i + 1) * nR + j;
      const d = (i + 1) * nR + j + 1;
      indices[p++] = a;
      indices[p++] = c;
      indices[p++] = b;
      indices[p++] = b;
      indices[p++] = c;
      indices[p++] = d;
    }
  }
  return { positions, colors, indices };
}

// Valley floor world points (slightly lifted so the line reads above the mesh).
export const valleyPoints = R.map((r, j) => [
  X(r),
  Y(valley.eStar[j]) + 0.03,
  ZC(valley.thetaStar[j]),
]);

// Dashed reference line a random start at the far geometry lands somewhere on.
export const randomLine = [
  [X(meta.rMax), 0.02, ZC(meta.thetaMin)],
  [X(meta.rMax), 0.02, ZC(meta.thetaMax)],
];

// ---- readout helpers ------------------------------------------------------
export const CHEM_ACC_MHA = 1.6;

// point on the valley floor at geometry index j
export function valleyReadout(j) {
  const e = valley.eStar[j];
  const ref = fciOnR ? fciOnR[j] : null;
  return {
    r: R[j],
    theta: valley.thetaStar[j],
    e,
    delta: ref == null ? null : (e - ref) * 1000,
    world: valleyPoints[j],
    onValley: true,
  };
}

// a blind guess: arbitrary theta index i at the far geometry
export function randomReadout(i) {
  const j = nR - 1;
  const e = Z[i][j];
  const ref = fciOnR ? fciOnR[j] : null;
  return {
    r: R[j],
    theta: TH[i],
    e,
    delta: ref == null ? null : (e - ref) * 1000,
    world: [X(R[j]), Y(e) + 0.03, ZC(TH[i])],
    onValley: false,
  };
}

export { meta };
