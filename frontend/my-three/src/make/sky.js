import * as THREE from "three";

// Simple vertical-gradient skydome via ShaderMaterial.
function makeSkyDome() {
  const geo = new THREE.SphereGeometry(1000, 32, 16);
  const mat = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    uniforms: {
      topColor:    { value: new THREE.Color(0x87ceeb) }, // light blue
      bottomColor: { value: new THREE.Color(0xffffff) }, // near-horizon
      offset:      { value: 33.0 },
      exponent:    { value: 0.6 }
    },
    vertexShader: `
      varying vec3 vWorldPosition;
      void main() {
        vec4 wp = modelMatrix * vec4(position, 1.0);
        vWorldPosition = wp.xyz;
        gl_Position = projectionMatrix * viewMatrix * wp;
      }
    `,
    fragmentShader: `
      uniform vec3 topColor;
      uniform vec3 bottomColor;
      uniform float offset;
      uniform float exponent;
      varying vec3 vWorldPosition;

      void main() {
        float h = normalize(vWorldPosition + vec3(0.0, offset, 0.0)).y;
        float t = pow(max(h, 0.0), exponent);
        gl_FragColor = vec4(mix(bottomColor, topColor, t), 1.0);
      }
    `
  });

  return new THREE.Mesh(geo, mat);
}

export { makeSkyDome };
