import * as THREE from "three";

export function makePlayer({
  radius,
  roadInner,
  roadOuter,
  baseY,
  roadHeight,
  size = 1.2,
  color = 0xff6b3d,
  smoothing = 8,
} = {}) {
  if (
    radius === undefined ||
    roadInner === undefined ||
    roadOuter === undefined ||
    baseY === undefined ||
    roadHeight === undefined
  ) {
    throw new Error("makePlayer requires radius, roadInner, roadOuter, baseY, roadHeight");
  }

  const geometry = new THREE.BoxGeometry(size, size, size);
  const material = new THREE.MeshStandardMaterial({ color, roughness: 0.6, metalness: 0.1 });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.castShadow = true;
  mesh.receiveShadow = true;

  const roadRadius = radius * (roadInner + roadOuter) * 0.5;
  const y = baseY + roadHeight + size * 0.5;

  let currentAngle = 0;
  let lastProgress = null;
  let lapOffset = 0;

  const update = (progress01, dtSeconds = 0.016) => {
    const p = Math.min(1, Math.max(0, progress01 || 0));
    if (lastProgress !== null) {
      const deltaP = p - lastProgress;
      if (deltaP < -0.5) lapOffset += 1;
      else if (deltaP > 0.5) lapOffset -= 1;
    }
    lastProgress = p;

    const continuousProgress = p + lapOffset;
    const targetAngle = continuousProgress * Math.PI * 2;

    // Smooth shortest-arc rotation
    let delta = targetAngle - currentAngle;
    delta = ((delta + Math.PI) % (Math.PI * 2)) - Math.PI;

    const t = 1 - Math.exp(-smoothing * dtSeconds);
    currentAngle += delta * t;

    mesh.position.set(Math.cos(currentAngle) * roadRadius, y, Math.sin(currentAngle) * roadRadius);
    mesh.rotation.y = -currentAngle + Math.PI * 0.5;
  };

  update(0);

  return { mesh, update };
}
