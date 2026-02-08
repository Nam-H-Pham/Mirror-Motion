import * as THREE from "three";

export function makeFog({
  color = 0xcfe9ff,
  type = "exp2",
  density = 0.0016,
  near = 40,
  far = 900,
} = {}) {
  const fogColor = new THREE.Color(color);
  const fog =
    type === "linear"
      ? new THREE.Fog(fogColor, near, far)
      : new THREE.FogExp2(fogColor, density);

  return { fog, color: fogColor };
}
