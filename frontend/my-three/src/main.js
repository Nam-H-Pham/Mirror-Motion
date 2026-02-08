import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { makeSkyDome } from "./make/sky.js";
import { makeOcean } from "./make/ocean.js";
import { makeFog } from "./make/fog.js";

const scene = new THREE.Scene();

const { fog, color: fogColor } = makeFog({
  color: 0xcfe9ff,
  density: 0.0028,
});
scene.fog = fog;

// Camera
const camera = new THREE.PerspectiveCamera(
  60,
  window.innerWidth / window.innerHeight,
  0.1,
  10000
);
camera.position.set(0, 30, 50);

// Renderer
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setClearColor(fogColor, 1);
document.body.style.margin = "0";
document.body.appendChild(renderer.domElement);

// Controls (AFTER camera + renderer exist)
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

// A mesh (flat circle)
const geometry = new THREE.CircleGeometry(32, 64); // radius 32, 64 segments for smoothness
geometry.rotateX(-Math.PI / 2); // lay flat (Y up)

const material = new THREE.MeshStandardMaterial({
  roughness: 0.4,
  metalness: 0.1,
  side: THREE.DoubleSide // so its visible from below too
});

const circle = new THREE.Mesh(geometry, material);
scene.add(circle);


// Light
const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
dirLight.position.set(2, 3, 2);
scene.add(dirLight);

scene.add(new THREE.AmbientLight(0xffffff, 0.3));

// Sky dome (rendered on the inside of a large sphere)
scene.add(makeSkyDome());

const ocean = makeOcean({ size: 1000, segments: 250, baseY: -2 });
scene.add(ocean.mesh);

// Good lighting helps the facets pop
const sun = new THREE.DirectionalLight(0xffffff, 1.2);
sun.position.set(50, 100, 30);
scene.add(sun);
scene.add(new THREE.AmbientLight(0xffffff, 0.35));


// Resize
window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});



// Animation loop
function animate(timeMs) {
  requestAnimationFrame(animate);

  ocean.update(timeMs * 0.0001);

  controls.update();          // update first when damping is on
  renderer.render(scene, camera);
}
animate();
