import * as THREE from "three";

export function makeOcean({
  size = 1200,
  segments = 180,
  baseY = 0,
  swellDirection = new THREE.Vector2(0.8, 0.2),
  swellDirection2 = new THREE.Vector2(0.3, 0.9),
} = {}) {
  const geometry = new THREE.PlaneGeometry(size, size, segments, segments);
  geometry.rotateX(-Math.PI / 2);

  const pos = geometry.attributes.position;
  const original = new Float32Array(pos.array.length);
  original.set(pos.array);

  // --- Vertex colours buffer (r,g,b per vertex)
  const colors = new Float32Array(pos.count * 3);
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));

  // Ocean palette (lighter, shallower feel)
  const deepColor = new THREE.Color(0x2d8ec4);
  const midColor = new THREE.Color(0x4bb6e8);
  const shallowColor = new THREE.Color(0x7ee4fb);
  const foamColor = new THREE.Color(0xf3fbff);

  const material = new THREE.MeshStandardMaterial({
    vertexColors: true,     // <-- key: use per-vertex shading
    roughness: 0.18,
    metalness: 0.0,
    transparent: true,      // optional: more watery feel
    opacity: 0.90,
  });

  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.y = baseY;
  mesh.receiveShadow = true;

  // Helpers
  const clamp01 = (v) => Math.min(1, Math.max(0, v));
  const smoothstep = (e0, e1, x) => {
    const t = clamp01((x - e0) / (e1 - e0));
    return t * t * (3 - 2 * t);
  };

  // Normalize directions
  const dir1 = swellDirection.clone().normalize();
  const dir2 = swellDirection2.clone().normalize();

  // Wave settings (scaled for large bodies of water)
  const swell1 = { amp: 1.6, length: 190, speed: 5.4, dir: dir1 };
  const swell2 = { amp: 1.0, length: 110, speed: 3.6, dir: dir2 };
  const chop = { amp: 0.35, length: 28, speed: 9.0 };
  const ripples = { amp: 0.18, length: 12, speed: 12.0 };

  const k1 = (Math.PI * 2) / swell1.length;
  const k2 = (Math.PI * 2) / swell2.length;
  const k3 = (Math.PI * 2) / chop.length;
  const k4 = (Math.PI * 2) / ripples.length;

  // Precompute approximate wave amplitude so we can normalise height into 0..1
  const approxAmp = swell1.amp + swell2.amp + chop.amp + ripples.amp;
  const invRange = 1 / (approxAmp * 2);
  const c = new THREE.Color();

  function update(tSeconds) {
    const t = tSeconds;

    for (let i = 0; i < pos.count; i++) {
      const ix = i * 3;
      const x = original[ix + 0];
      const y0 = original[ix + 1];
      const z = original[ix + 2];

      // Two large swells + chop + ripples for convincing motion at scale
      const d1 = x * dir1.x + z * dir1.y;
      const d2 = x * dir2.x + z * dir2.y;

      // Large-scale irregularity to break distant repetition
      const warp = Math.sin((x * 0.05) + (z * 0.03) + t * 0.15) * 25.0;
      const warp2 = Math.cos((x * 0.04) - (z * 0.06) - t * 0.12) * 18.0;
      const gust = 0.85 + Math.sin((x * 0.002) + (z * 0.0015) + t * 0.08) * 0.2;

      const wave1 = Math.sin((d1 + warp) * k1 + t * swell1.speed) * swell1.amp * gust;
      const wave2 = Math.sin((d2 + warp2) * k2 + t * swell2.speed + 0.8) * swell2.amp;
      const wave3 = Math.sin((x + z + warp * 0.4) * k3 - t * chop.speed) * chop.amp;
      const wave4 = Math.sin((x - z + warp2 * 0.3) * k4 + t * ripples.speed) * ripples.amp;

      const y = y0 + wave1 + wave2 + wave3 + wave4;
      pos.array[ix + 1] = y;

      // --- Colouring based on height (more shades = more depth)
      // normalise height into [0..1]
      const h01 = clamp01((y - (y0 - approxAmp)) * invRange);

      // add subtle spatial variation so it doesn't look too uniform
      const variation = (Math.sin(x * 0.015 + z * 0.02) * 0.5 + 0.5) * 0.08; // 0..0.08
      const hVar = clamp01(h01 + variation);

      // blend deep -> mid -> shallow
      // (two-stage blend gives nicer palette control than a single lerp)
      const midMix = smoothstep(0.10, 0.55, hVar);
      const shallowMix = smoothstep(0.50, 0.88, hVar);

      c.copy(deepColor).lerp(midColor, midMix).lerp(shallowColor, shallowMix);

      // optional "foam" tint on the very top crests
      const foam = smoothstep(0.90, 0.985, hVar);
      c.lerp(foamColor, foam * 0.7);

      colors[ix + 0] = c.r;
      colors[ix + 1] = c.g;
      colors[ix + 2] = c.b;
    }

    pos.needsUpdate = true;
    geometry.attributes.color.needsUpdate = true;
    geometry.computeVertexNormals();
  }

  return { mesh, update };
}
