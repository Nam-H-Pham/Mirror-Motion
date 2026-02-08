import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { makeSkyDome } from "./make/sky.js";
import { makeOcean } from "./make/ocean.js";
import { makeFog } from "./make/fog.js";
import { makeIsland } from "./make/island.js";
import { makePlayer } from "./make/player.js";

const scene = new THREE.Scene();

const { fog, color: fogColor } = makeFog({
  color: 0xcfe9ff,
  density: 0.0048,
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

const islandParams = {
  radius: 32,
  segments: 200,
  baseY: -1.2,
  height: 10,
  roadInner: 0.68,
  roadOuter: 0.76,
  roadHeight: 2,
};
const island = makeIsland(islandParams);
scene.add(island.mesh);

const player = makePlayer(islandParams);
scene.add(player.mesh);


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

// API polling
const API_BASE = "http://127.0.0.1:8000";
const POLL_MS = 100;
let latestLapProgress = 0;

function normalizeProgress(data) {
  if (typeof data === "number") return data;
  if (data && typeof data.current_lap_progress === "number") return data.current_lap_progress;
  return 0;
}

async function pollLapProgress() {
  try {
    const res = await fetch(`${API_BASE}/current_lap_progress`, { cache: "no-store" });
    if (!res.ok) return;
    const data = await res.json();
    latestLapProgress = normalizeProgress(data);
  } catch (err) {
    // ignore transient errors
  }
}

setInterval(pollLapProgress, POLL_MS);
pollLapProgress();



let lastTimeMs = 0;

// Animation loop
function animate(timeMs) {
  requestAnimationFrame(animate);

  ocean.update(timeMs * 0.0001);
  const dtSeconds = Math.min(0.05, (timeMs - lastTimeMs) * 0.001 || 0);
  lastTimeMs = timeMs;
  player.update(latestLapProgress, dtSeconds);

  controls.update();          // update first when damping is on
  renderer.render(scene, camera);
}
animate();
