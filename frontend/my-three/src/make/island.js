import * as THREE from "three";

export function makeIsland({
  radius = 32,
  segments = 160,
  baseY = 0,
  height = 6,
  edgeDrop = 2.2,
  noiseAmp = 2.0,
  noiseScale = 0.03,
  plateauRadius = 0.28,
  plateauHeight = 0.88,
  beachWidth = 0.08,
  beachHeight = 0.2,
  craterRadius = 0.12,
  craterDepth = 2.4,
  craterRim = 0.05,
  roadInner = 0.68,
  roadOuter = 0.76,
  roadHeight = 2,
} = {}) {
  const size = radius * 2;
  const geometry = new THREE.PlaneGeometry(size, size, segments, segments);
  geometry.rotateX(-Math.PI / 2);

  const pos = geometry.attributes.position;
  const colors = new Float32Array(pos.count * 3);
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));

  const sand = new THREE.Color(0xe7d9b3);
  const sandLight = new THREE.Color(0xf3e9c7);
  const grass = new THREE.Color(0x4f9a4d);
  const rock = new THREE.Color(0xe0e0e0);
  const road = new THREE.Color(0x3d3c3c);
  const c = new THREE.Color();

  const clamp01 = (v) => Math.min(1, Math.max(0, v));
  const smoothstep = (e0, e1, x) => {
    const t = clamp01((x - e0) / (e1 - e0));
    return t * t * (3 - 2 * t);
  };
  const lerp = (a, b, t) => a + (b - a) * t;

  // 2D value noise + fBm for layered terrain detail.
  const hash = (ix, iz) => {
    const s = Math.sin(ix * 127.1 + iz * 311.7) * 43758.5453;
    return s - Math.floor(s);
  };
  const valueNoise2 = (x, z) => {
    const x0 = Math.floor(x);
    const z0 = Math.floor(z);
    const x1 = x0 + 1;
    const z1 = z0 + 1;
    const fx = x - x0;
    const fz = z - z0;
    const u = fx * fx * (3 - 2 * fx);
    const v = fz * fz * (3 - 2 * fz);
    const a = hash(x0, z0);
    const b = hash(x1, z0);
    const c0 = hash(x0, z1);
    const d = hash(x1, z1);
    return lerp(lerp(a, b, u), lerp(c0, d, u), v) * 2 - 1;
  };
  const fbm = (x, z) => {
    let amp = 1.0;
    let freq = 1.0;
    let sum = 0.0;
    let norm = 0.0;
    for (let i = 0; i < 4; i++) {
      sum += valueNoise2(x * freq, z * freq) * amp;
      norm += amp;
      amp *= 0.5;
      freq *= 2.2;
    }
    return sum / norm;
  };

  for (let i = 0; i < pos.count; i++) {
    const ix = i * 3;
    let x = pos.array[ix + 0];
    let z = pos.array[ix + 2];

    // Clamp vertices to a circular boundary to keep a gridded topology
    const rRaw = Math.sqrt(x * x + z * z);
    if (rRaw > radius) {
      const s = radius / rRaw;
      x *= s;
      z *= s;
      pos.array[ix + 0] = x;
      pos.array[ix + 2] = z;
    }

    const r = Math.sqrt(x * x + z * z);
    const r01 = clamp01(r / radius);

    // Radial profile with a flattened top and steeper shoreline.
    const profile = Math.pow(1 - r01, 1.35);
    const plateauMask = 1 - smoothstep(0.0, plateauRadius, r01);
    let baseProfile = lerp(profile, plateauHeight, plateauMask);

    // Volcanic crater: inset center + slight rim lift
    const craterInner = smoothstep(0.0, craterRadius, r01);
    const craterBowl = (1 - craterInner) * (1 - craterInner);
    baseProfile -= craterBowl * (craterDepth / Math.max(height, 0.001));

    // Noise detail: broad undulations + ridge-like breakup.
    const macro = fbm(x * noiseScale, z * noiseScale);
    const ridge = 1 - Math.abs(fbm(x * noiseScale * 2.6, z * noiseScale * 2.6));
    const detail = macro * 0.7 + (ridge - 0.5) * 0.9;

    const midMask = smoothstep(0.12, 0.85, r01);
    const edgeMask = smoothstep(0.6, 1.0, r01);

    let y = baseY + baseProfile * height;
    y += detail * noiseAmp * midMask;
    y -= edgeDrop * edgeMask * edgeMask;

    // Beach shelf near the rim (do not fully flatten the outer ring).
    const beachMask = smoothstep(1 - beachWidth, 1.0, r01);

    // Flat ring road (blend to a constant height)
    const roadBand = smoothstep(roadInner, roadInner + 0.02, r01) *
      (1 - smoothstep(roadOuter - 0.02, roadOuter, r01));
    y = lerp(y, baseY + roadHeight, roadBand);

    pos.array[ix + 1] = y;

    // Color by height, with lighter sand at the beach.
    const h01 = clamp01((y - (baseY - edgeDrop)) / (height + edgeDrop));
    const grassMix = smoothstep(0.2, 0.6, h01);
    const rockMix = smoothstep(0.6, 0.95, h01);
    c.copy(sand).lerp(grass, grassMix).lerp(rock, rockMix);
    c.lerp(sandLight, beachMask * 0.7);
    if (roadBand > 0.0) c.lerp(road, roadBand * 0.8);

    colors[ix + 0] = c.r;
    colors[ix + 1] = c.g;
    colors[ix + 2] = c.b;
  }

  pos.needsUpdate = true;
  geometry.attributes.color.needsUpdate = true;
  geometry.computeVertexNormals();

  const material = new THREE.MeshStandardMaterial({
    vertexColors: true,
    roughness: 0.85,
    metalness: 0.02,
  });

  const mesh = new THREE.Mesh(geometry, material);
  mesh.castShadow = true;
  mesh.receiveShadow = true;

  return { mesh };
}
