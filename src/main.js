import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { Line2 } from 'three/examples/jsm/lines/Line2.js';
import { LineGeometry } from 'three/examples/jsm/lines/LineGeometry.js';
import { LineMaterial } from 'three/examples/jsm/lines/LineMaterial.js';
import { CSS2DRenderer, CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { Sky } from 'three/examples/jsm/objects/Sky.js';
import campus from './data/campus.json';
import blockNames from './data/blockNames.js';

const LAT0 = 4.3385;
const LON0 = 101.1370;
const CAMPUS_RADIUS = 5000; // User-approved filter: the download contains multiple campuses.
const LABEL_DISTANCE = 1800; // Camera-to-label distance in metres; zoom in to reveal names.
const HERITAGE_ID = 403039202;
const longitudeScale = 111320 * Math.cos(LAT0 * Math.PI / 180);
const project = ({ lat, lon }) => ({
  x: (lon - LON0) * longitudeScale,
  z: -(lat - LAT0) * 110540,
});
const ways = campus.elements.filter(element => element.type === 'way');
const buildings = ways.filter(way => way.tags?.building);
const paths = ways.filter(way => way.tags?.highway);
const hasGeometry = (way, minimumPoints = 3) => way.geometry?.length >= minimumPoints && way.geometry.every(point =>
  Number.isFinite(point.lat) && Number.isFinite(point.lon));
const isNearCampus = way => way.geometry.every(point => {
  const { x, z } = project(point);
  return Math.hypot(x, z) <= CAMPUS_RADIUS;
});
const campusBuildings = buildings.filter(way => hasGeometry(way) && isNearCampus(way));
const campusPaths = paths.filter(way => hasGeometry(way, 2) && isNearCampus(way));

export function buildWalkwayGraph(pathWays) {
  const nodes = new Map();
  let edgeCount = 0;
  let fallbackWays = 0;
  for (const way of pathWays) {
    if (!hasGeometry(way, 2)) continue;
    const hasNodeIds = way.nodes !== undefined;
    if (hasNodeIds && (!Array.isArray(way.nodes) || way.nodes.length !== way.geometry.length ||
        way.nodes.some(id => !Number.isSafeInteger(id)))) {
      throw new Error(`Highway way ${way.id} has invalid or misaligned OSM node IDs.`);
    }
    if (!hasNodeIds) fallbackWays++;
    const keys = way.geometry.map((point, index) => {
      const { x, z } = project(point);
      // IDs are authoritative: nearby paths and geometric crossings do not imply a join.
      // Coordinate buckets are used only when the way has no nodes array.
      const key = hasNodeIds ? way.nodes[index] : `${x.toFixed(1)},${z.toFixed(1)}`;
      if (!nodes.has(key)) nodes.set(key, { x, z, neighbors: new Map() });
      return key;
    });
    for (let i = 1; i < keys.length; i++) {
      const fromKey = keys[i - 1];
      const toKey = keys[i];
      if (fromKey === toKey) continue;
      const from = nodes.get(fromKey);
      const to = nodes.get(toKey);
      const distance = Math.hypot(to.x - from.x, to.z - from.z);
      if (!from.neighbors.has(toKey)) edgeCount++;
      from.neighbors.set(toKey, distance);
      to.neighbors.set(fromKey, distance);
    }
  }

  const visited = new Set();
  const componentSizes = [];
  for (const key of nodes.keys()) {
    if (visited.has(key)) continue;
    const stack = [key];
    visited.add(key);
    let size = 0;
    while (stack.length) {
      const current = nodes.get(stack.pop());
      current.component = componentSizes.length;
      size++;
      for (const neighbor of current.neighbors.keys()) {
        if (visited.has(neighbor)) continue;
        visited.add(neighbor);
        stack.push(neighbor);
      }
    }
    componentSizes.push(size);
  }
  const largestComponentSize = Math.max(0, ...componentSizes);
  const largestComponentFraction = nodes.size ? largestComponentSize / nodes.size : 0;
  return {
    nodes, edgeCount, componentSizes, largestComponentSize, largestComponentFraction,
    connectedEnough: nodes.size > 0 && largestComponentFraction >= 0.5,
    fallbackWays,
  };
}

export let walkwayGraph;
export const navigation = { origin: null, destination: null, route: null };
export let campusView;

export function nearestGraphNode(graph, point) {
  let key = null;
  let distance = Infinity;
  for (const [candidate, node] of graph.nodes) {
    const candidateDistance = Math.hypot(node.x - point.x, node.z - point.z);
    if (candidateDistance < distance) {
      key = candidate;
      distance = candidateDistance;
    }
  }
  return { key, distance };
}

export function findRoute(graph, start, goal) {
  if (!graph.nodes.has(start) || !graph.nodes.has(goal)) return null;
  if (graph.nodes.get(start).component !== graph.nodes.get(goal).component) return null;
  const target = graph.nodes.get(goal);
  const heuristic = key => {
    const node = graph.nodes.get(key);
    return Math.hypot(node.x - target.x, node.z - target.z);
  };
  // A linear open-set scan is sufficient for this 1,632-node demo graph.
  const open = new Set([start]);
  const cameFrom = new Map();
  const distances = new Map([[start, 0]]);
  const scores = new Map([[start, heuristic(start)]]);
  while (open.size) {
    let current;
    let bestScore = Infinity;
    for (const key of open) {
      if (scores.get(key) < bestScore) {
        bestScore = scores.get(key);
        current = key;
      }
    }
    if (current === goal) {
      const keys = [goal];
      while (cameFrom.has(keys[keys.length - 1])) keys.push(cameFrom.get(keys[keys.length - 1]));
      return { keys: keys.reverse(), distance: distances.get(goal) };
    }
    open.delete(current);
    for (const [neighbor, weight] of graph.nodes.get(current).neighbors) {
      const candidateDistance = distances.get(current) + weight;
      if (candidateDistance >= (distances.get(neighbor) ?? Infinity)) continue;
      cameFrom.set(neighbor, current);
      distances.set(neighbor, candidateDistance);
      scores.set(neighbor, candidateDistance + heuristic(neighbor));
      open.add(neighbor);
    }
  }
  return null;
}

try {
  walkwayGraph = buildWalkwayGraph(campusPaths);
  const graphSummary = {
    nodeCount: walkwayGraph.nodes.size,
    edgeCount: walkwayGraph.edgeCount,
    largestComponentSize: walkwayGraph.largestComponentSize,
    largestComponentPercent: Number((walkwayGraph.largestComponentFraction * 100).toFixed(1)),
    componentCount: walkwayGraph.componentSizes.length,
    highwayWays: campusPaths.length,
    coordinateFallbackWays: walkwayGraph.fallbackWays,
  };
  console.info('Milestone 2: undirected walkway graph', graphSummary);
  console.table(graphSummary);
  document.querySelector('#node-count').textContent = graphSummary.nodeCount.toLocaleString();
  document.querySelector('#edge-count').textContent = graphSummary.edgeCount.toLocaleString();
  document.querySelector('#component-summary').textContent = `${graphSummary.largestComponentSize.toLocaleString()} / ${graphSummary.nodeCount.toLocaleString()} nodes (${graphSummary.largestComponentPercent}%) in the largest component · ${graphSummary.componentCount} components total.`;
  document.querySelector('#graph-check').textContent = walkwayGraph.connectedEnough
    ? 'Connectivity check passed · shared OSM nodes'
    : 'STOP: largest component below 50%. Check path joins.';
  document.querySelector('#graph-check').classList.toggle('blocked', !walkwayGraph.connectedEnough);
  if (!walkwayGraph.connectedEnough) {
    console.error('STOP: largest connected component is below 50% of all nodes. Investigate join logic before wayfinding.', graphSummary);
  }
  if (!campusBuildings.length) throw new Error('No usable building footprints within 5 km of the supplied Kampar centre.');

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#101e26');
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.25;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  // Procedural daylight for architectural reflections; no external image asset.
  const environmentScene = new THREE.Scene();
  const environmentSky = new Sky();
  environmentSky.scale.setScalar(1000);
  environmentSky.material.uniforms.turbidity.value = 3;
  environmentSky.material.uniforms.rayleigh.value = 1.5;
  environmentSky.material.uniforms.sunPosition.value.set(-0.6, 0.8, 0.6).normalize();
  environmentScene.add(environmentSky);
  const environmentGenerator = new THREE.PMREMGenerator(renderer);
  const daylightEnvironment = environmentGenerator.fromScene(environmentScene, 0.04);
  scene.environment = daylightEnvironment.texture;
  environmentGenerator.dispose();
  environmentSky.geometry.dispose();
  environmentSky.material.dispose();
  document.querySelector('#map').appendChild(renderer.domElement);
  const labelRenderer = new CSS2DRenderer();
  labelRenderer.setSize(window.innerWidth, window.innerHeight);
  labelRenderer.domElement.id = 'map-labels';
  document.querySelector('#map').appendChild(labelRenderer.domElement);
  const buildingLabels = [];
  const labelPosition = new THREE.Vector3();

  const sky = new THREE.HemisphereLight('#e2f4ff', '#526467', 2.4);
  scene.add(sky);
  const sun = new THREE.DirectionalLight('#fff1d5', 3);
  sun.position.set(-600, 1000, 400);
  scene.add(sun);

  const buildingGroup = new THREE.Group();
  scene.add(buildingGroup);
  const buildingMaterial = new THREE.MeshStandardMaterial({
    color: '#c9d7ce', roughness: 0.85, metalness: 0, envMapIntensity: 0.025,
  });
  const edgeMaterial = new THREE.LineBasicMaterial({
    color: '#435f60', transparent: true, opacity: 0.45,
  });
  for (const way of campusBuildings) {
    // Rotation sends shape Y to world -Z; negate projected Z to preserve north.
    const points = way.geometry.map(point => {
      const { x, z } = project(point);
      return new THREE.Vector2(x, -z);
    });
    if (points[0].equals(points[points.length - 1])) points.pop();
    if (points.length < 3) continue;
    const shape = new THREE.Shape(points);
    const geometry = new THREE.ExtrudeGeometry(shape, {
      depth: (Number(way.tags['building:levels']) || 3) * 3.5,
      bevelEnabled: false,
    });
    geometry.rotateX(-Math.PI / 2);
    const building = new THREE.Mesh(geometry, buildingMaterial.clone());
    geometry.computeBoundingBox();
    const buildingCentre = geometry.boundingBox.getCenter(new THREE.Vector3());
    const name = (Object.hasOwn(blockNames, way.id) ? blockNames[way.id] : way.tags.name) || '';
    building.userData = {
      id: way.id, tags: way.tags, name, centre: buildingCentre,
      snap: nearestGraphNode(walkwayGraph, buildingCentre),
    };
    building.add(new THREE.LineSegments(new THREE.EdgesGeometry(geometry), edgeMaterial));
    if (name) {
      const element = document.createElement('div');
      element.className = 'building-label';
      element.textContent = name;
      const label = new CSS2DObject(element);
      label.position.set(buildingCentre.x, geometry.boundingBox.max.y + 8, buildingCentre.z);
      label.center.set(0.5, 1);
      label.visible = false;
      building.add(label);
      buildingLabels.push(label);
    }
    buildingGroup.add(building);
  }

  // Draw the same highway ways used by the graph, including two-point links.
  const pathVertices = [];
  for (const way of campusPaths) {
    const points = way.geometry.map(project);
    for (let i = 1; i < points.length; i++) {
      pathVertices.push(points[i - 1].x, 0.15, points[i - 1].z, points[i].x, 0.15, points[i].z);
    }
  }
  const pathGeometry = new THREE.BufferGeometry();
  pathGeometry.setAttribute('position', new THREE.Float32BufferAttribute(pathVertices, 3));
  const pathLines = new THREE.LineSegments(pathGeometry, new THREE.LineBasicMaterial({ color: '#4e777b' }));
  scene.add(pathLines);

  const bounds = new THREE.Box3().setFromObject(buildingGroup);
  if (pathVertices.length) bounds.expandByObject(pathLines);
  const centre = bounds.getCenter(new THREE.Vector3());
  const size = bounds.getSize(new THREE.Vector3());
  const span = Math.max(size.x, size.z, 100);
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(span * 8, span * 8),
    new THREE.MeshStandardMaterial({ color: '#172c33', roughness: 1, envMapIntensity: 0.025 }),
  );
  ground.rotation.x = -Math.PI / 2;
  ground.position.set(centre.x, -0.6, centre.z);
  ground.receiveShadow = true;
  scene.add(ground);
  const grid = new THREE.GridHelper(Math.ceil(span / 100) * 100 + 400, Math.ceil(span / 100) + 4, '#29464c', '#29464c');
  grid.position.set(centre.x, 0, centre.z);
  grid.material.transparent = true;
  grid.material.opacity = 0.28;
  scene.add(grid);
  scene.fog = new THREE.Fog('#101e26', span * 3, span * 7);

  const camera = new THREE.PerspectiveCamera(42, window.innerWidth / window.innerHeight, 0.5, span * 20);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.07;
  controls.maxPolarAngle = Math.PI / 2 - 0.06;
  controls.minDistance = 30;
  controls.maxDistance = span * 6;
  controls.screenSpacePanning = false;
  let inspecting = false;
  let heritageModel = null;
  let heritageSite = null;
  let siteMetadata = null;
  let surroundingsVisible = true;
  let activeView = 'elevated';
  let inspectionFrame = null;
  const heritageBuilding = buildingGroup.children.find(building => building.userData.id === HERITAGE_ID);

  const routeGroup = new THREE.Group();
  scene.add(routeGroup);
  const routeMaterial = new LineMaterial({ color: '#56f1d2', linewidth: 5 });
  routeMaterial.resolution.set(window.innerWidth, window.innerHeight);
  const marker = new THREE.Mesh(
    new THREE.SphereGeometry(7, 16, 12),
    new THREE.MeshBasicMaterial({ color: '#ffffff' }),
  );
  marker.visible = false;
  scene.add(marker);
  let routePoints = [];
  let cumulativeDistances = [];
  let animationStarted = 0;
  campusView = { camera, buildingGroup, routeGroup, marker };
  const routeMessage = document.querySelector('#route-message');
  const routeDistance = document.querySelector('#route-distance');
  const buildingTitle = building => building.userData.name || `OSM way ${building.userData.id}`;
  const clearRoute = () => {
    for (const child of [...routeGroup.children]) {
      routeGroup.remove(child);
      child.geometry.dispose();
      if (child.material !== routeMaterial) child.material.dispose();
    }
    marker.visible = false;
    routePoints = [];
    cumulativeDistances = [];
    navigation.route = null;
    routeDistance.textContent = '—';
    document.querySelector('#snap-note').textContent = '';
  };
  const refreshSelection = () => {
    for (const building of buildingGroup.children) {
      building.material.color.set(building === navigation.origin ? '#56f1d2'
        : building === navigation.destination ? '#ffc17c' : '#c9d7ce');
    }
    if (heritageModel) {
      const selectedColour = heritageBuilding === navigation.origin ? '#56f1d2'
        : heritageBuilding === navigation.destination ? '#ffc17c' : '#000000';
      heritageModel.traverse(object => {
        if (object.isMesh && object.material.emissive) {
          object.material.emissive.set(selectedColour);
          object.material.emissiveIntensity = 0.2;
        }
      });
    }
    for (const label of buildingLabels) {
      label.element.classList.toggle('is-origin', label.parent === navigation.origin);
      label.element.classList.toggle('is-destination', label.parent === navigation.destination);
    }
    document.querySelector('#origin-name').textContent = navigation.origin ? buildingTitle(navigation.origin) : 'Click a building';
    document.querySelector('#destination-name').textContent = navigation.destination ? buildingTitle(navigation.destination) : 'Then click another';
    document.querySelector('#clear-route').disabled = !navigation.origin;
  };
  const selectBuilding = building => {
    if (inspecting) return;
    if (!walkwayGraph.connectedEnough) {
      routeMessage.textContent = 'Routing stopped: graph connectivity check failed.';
      return;
    }
    if (!navigation.origin || navigation.destination) {
      clearRoute();
      navigation.origin = building;
      navigation.destination = null;
      routeMessage.textContent = 'Origin selected. Click another building for your destination.';
      refreshSelection();
      return;
    }
    if (building === navigation.origin) {
      routeMessage.textContent = 'Choose a different building for your destination.';
      return;
    }
    clearRoute();
    navigation.destination = building;
    refreshSelection();
    const start = navigation.origin.userData.snap;
    const goal = navigation.destination.userData.snap;
    const route = findRoute(walkwayGraph, start.key, goal.key);
    document.querySelector('#snap-note').textContent = `Nearest-node offsets from building centres: ${Math.round(start.distance)} m / ${Math.round(goal.distance)} m. Distance covers graph edges only.`;
    if (!route) {
      routeMessage.textContent = 'No route: the nearest path nodes are in disconnected components. Click a building to start again.';
      return;
    }
    navigation.route = route;
    routeDistance.textContent = `${Math.round(route.distance).toLocaleString()} m`;
    routePoints = route.keys.map(key => {
      const node = walkwayGraph.nodes.get(key);
      return new THREE.Vector3(node.x, 2.5, node.z);
    });
    cumulativeDistances = [0];
    for (let i = 1; i < routePoints.length; i++) {
      cumulativeDistances.push(cumulativeDistances[i - 1] + routePoints[i - 1].distanceTo(routePoints[i]));
    }
    if (routePoints.length > 1 && route.distance > 0) {
      const geometry = new LineGeometry();
      geometry.setPositions(routePoints.flatMap(point => [point.x, point.y, point.z]));
      // Straight segments follow the graph exactly, without smoothing across corners.
      routeGroup.add(new Line2(geometry, routeMaterial));
    }
    for (const [index, colour] of [[0, '#56f1d2'], [routePoints.length - 1, '#ffc17c']]) {
      const endpoint = new THREE.Mesh(new THREE.SphereGeometry(6, 12, 8), new THREE.MeshBasicMaterial({ color: colour }));
      endpoint.position.copy(routePoints[index]);
      routeGroup.add(endpoint);
    }
    marker.position.copy(routePoints[0]);
    marker.visible = true;
    animationStarted = performance.now();
    routeMessage.textContent = route.distance > 0
      ? 'Route ready. The white marker follows the path. Click a building to start a new route.'
      : 'Both buildings snap to the same path node: 0 m along the graph. Click a building to start again.';
    console.info('Milestone 3: route found', {
      origin: navigation.origin.userData.id, destination: building.userData.id,
      distanceMetres: route.distance, pathNodes: route.keys.length,
    });
  };
  document.querySelector('#clear-route').addEventListener('click', () => {
    clearRoute();
    navigation.origin = null;
    navigation.destination = null;
    refreshSelection();
    routeMessage.textContent = 'Click a building to choose your origin.';
  });

  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  const pickBuilding = event => {
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.set((event.clientX - rect.left) / rect.width * 2 - 1, -(event.clientY - rect.top) / rect.height * 2 + 1);
    raycaster.setFromCamera(pointer, camera);
    const hit = raycaster.intersectObjects(buildingGroup.children.filter(building => building.visible), true)
      .find(hit => hit.object.isMesh);
    if (!hit) return undefined;
    let building = hit.object;
    while (building.parent && building.parent !== buildingGroup) building = building.parent;
    return building.parent === buildingGroup ? building : undefined;
  };
  let press = null;
  renderer.domElement.addEventListener('pointerdown', event => {
    if (!event.isPrimary) { press = null; return; }
    if (event.button === 0) press = { id: event.pointerId, x: event.clientX, y: event.clientY, dragged: false };
  });
  renderer.domElement.addEventListener('pointermove', event => {
    if (press && Math.hypot(event.clientX - press.x, event.clientY - press.y) > 5) press.dragged = true;
    renderer.domElement.style.cursor = event.buttons ? 'grabbing' : pickBuilding(event) ? 'pointer' : 'grab';
  });
  renderer.domElement.addEventListener('pointerup', event => {
    const clicked = press && press.id === event.pointerId && !press.dragged && event.button === 0;
    press = null;
    if (!clicked) return;
    const building = pickBuilding(event);
    if (building) selectBuilding(building);
  });
  renderer.domElement.addEventListener('pointercancel', () => { press = null; });
  renderer.domElement.style.cursor = 'grab';

  const setInspection = enabled => {
    inspecting = enabled;
    document.body.classList.toggle('inspecting', enabled);
    document.querySelector('#model-review').hidden = !enabled;
    for (const building of buildingGroup.children) building.visible = !enabled || building === heritageBuilding;
    pathLines.visible = !enabled;
    routeGroup.visible = !enabled;
    if (enabled) document.querySelector('#clear-route').click();
    grid.visible = !enabled;
    scene.background.set(enabled ? '#bdcdd2' : '#101e26');
    scene.fog = enabled ? new THREE.Fog('#bdcdd2', 300, 1100) : new THREE.Fog('#101e26', span * 3, span * 7);
    ground.material.color.set(enabled ? '#6b7959' : '#172c33');
    sky.intensity = enabled ? 2.0 : 2.4;
    sun.intensity = enabled ? 3.1 : 3;
    sun.castShadow = enabled;
    renderer.toneMappingExposure = enabled ? 1.05 : 1.25;
    controls.minDistance = enabled ? 3 : 30;
    controls.maxPolarAngle = Math.PI / 2 - (enabled ? 0.015 : 0.06);
    controls.autoRotate = false;
    document.querySelector('#rotate-model').setAttribute('aria-pressed', 'false');
    document.querySelector('#status').textContent = enabled ? 'Heritage Hall · Architecture & landscape' : 'Campus overview · 49 buildings';
  };
  // Frame the model in the space beside/below the review panel, rather than
  // centring the architecture behind the UI. Off-axis projection keeps the
  // orbit target on the building when the panel is collapsed or resized.
  const frameInspectionViewport = () => {
    const width = window.innerWidth;
    const height = window.innerHeight;
    if (!inspecting) {
      camera.clearViewOffset();
      inspectionFrame = null;
      return null;
    }
    const panel = document.querySelector('#model-review').getBoundingClientRect();
    const toolbar = document.querySelector('.toolbar').getBoundingClientRect();
    const left = width > 640 ? panel.right + 20 : 16;
    const top = width > 640 ? 80 : panel.bottom + 16;
    const frameWidth = Math.max(80, width - left - 16);
    const frameHeight = Math.max(80, toolbar.top - 16 - top);
    const halfFov = THREE.MathUtils.degToRad(camera.fov / 2);
    const halfAngle = Math.atan(Math.tan(halfFov) * Math.min(frameHeight / height, frameWidth / height));
    if (inspectionFrame) {
      // Preserve the user's zoom and orbit when the available review area changes.
      const distanceScale = Math.sin(inspectionFrame.halfAngle) / Math.sin(halfAngle);
      camera.position.sub(controls.target).multiplyScalar(distanceScale).add(controls.target);
    }
    camera.setViewOffset(width, height,
      width / 2 - (left + frameWidth / 2), height / 2 - (top + frameHeight / 2), width, height);
    inspectionFrame = { halfAngle };
    return inspectionFrame;
  };
  const focusHeritage = (view = 'elevated') => {
    if (!heritageModel) return;
    setInspection(true);
    activeView = view;
    const modelBounds = new THREE.Box3().setFromObject(heritageModel);
    const target = modelBounds.getCenter(new THREE.Vector3());
    let radius = modelBounds.getSize(new THREE.Vector3()).length() / 2;
    if (view === 'entrance') {
      target.set(heritageModel.position.x, 4.8, heritageModel.position.z + 34);
      radius = 10.5;
    } else if (view === 'facade') {
      target.set(heritageModel.position.x + 13, 9, heritageModel.position.z + 29);
      radius = 24;
    } else if (view === 'site') {
      target.set(heritageModel.position.x - 4, 5, heritageModel.position.z + 35);
      radius = 134;
    } else if (view === 'arrival') {
      target.set(heritageModel.position.x, 4.2, heritageModel.position.z + 27);
      radius = 45;
    } else if (view === 'sculpture' && siteMetadata) {
      target.set(heritageModel.position.x + siteMetadata.sculpture.x, 1.4,
        heritageModel.position.z + siteMetadata.sculpture.z);
      radius = 5.2;
    }
    const { halfAngle } = frameInspectionViewport();
    const distance = view === 'arrival' ? 80 : radius / Math.sin(halfAngle) * 1.08;
    const directions = {
      front: new THREE.Vector3(0, 0.12, 1),
      rear: new THREE.Vector3(0, 0.22, -1),
      side: new THREE.Vector3(1, 0.22, 0),
      elevated: new THREE.Vector3(0.8, 0.65, 1),
      entrance: new THREE.Vector3(0.3, 0.07, 1),
      facade: new THREE.Vector3(0.5, 0.2, 1),
      site: new THREE.Vector3(0.7, 0.82, 1),
      arrival: new THREE.Vector3(0.01, 0.016, 1),
      sculpture: new THREE.Vector3(-0.65, 0.32, -1),
    };
    controls.target.copy(target);
    camera.position.copy(target).add(directions[view].normalize().multiplyScalar(distance));
    camera.near = view === 'sculpture' ? 0.1 : 0.4;
    camera.far = 3000;
    camera.updateProjectionMatrix();
    controls.update();
    document.querySelectorAll('[data-model-view]').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.modelView === view));
    });
  };

  const resetView = () => {
    setInspection(false);
    frameInspectionViewport();
    camera.near = 0.5;
    const radius = size.length() / 2;
    const verticalFov = THREE.MathUtils.degToRad(camera.fov);
    const horizontalFov = 2 * Math.atan(Math.tan(verticalFov / 2) * camera.aspect);
    const distance = radius / Math.sin(Math.min(verticalFov, horizontalFov) / 2) * 1.12;
    controls.maxDistance = Math.max(span * 6, distance * 1.5);
    camera.far = Math.max(span * 20, distance * 4);
    camera.updateProjectionMatrix();
    controls.target.copy(centre);
    camera.position.copy(centre).add(new THREE.Vector3(0.65, 1.15, 1).normalize().multiplyScalar(distance));
    controls.update();
  };
  resetView();
  document.querySelector('#reset').addEventListener('click', () => inspecting ? focusHeritage(activeView) : resetView());
  document.querySelector('#campus-overview').addEventListener('click', resetView);
  document.querySelector('#inspect-heritage').addEventListener('click', () => focusHeritage());
  document.querySelector('#toggle-surroundings').addEventListener('click', event => {
    surroundingsVisible = !surroundingsVisible;
    if (heritageSite) heritageSite.visible = surroundingsVisible;
    event.currentTarget.setAttribute('aria-pressed', String(surroundingsVisible));
    event.currentTarget.textContent = surroundingsVisible ? 'Hide surroundings' : 'Show surroundings';
  });
  document.querySelectorAll('[data-model-view]').forEach(button => {
    button.addEventListener('click', () => focusHeritage(button.dataset.modelView));
  });
  document.querySelector('#rotate-model').addEventListener('click', event => {
    controls.autoRotate = !controls.autoRotate;
    controls.autoRotateSpeed = 0.65;
    event.currentTarget.setAttribute('aria-pressed', String(controls.autoRotate));
  });
  document.querySelector('#toggle-review').addEventListener('click', event => {
    const details = document.querySelector('#model-review-details');
    details.hidden = !details.hidden;
    event.currentTarget.setAttribute('aria-expanded', String(!details.hidden));
    event.currentTarget.textContent = details.hidden ? 'Show info' : 'Hide info';
    frameInspectionViewport();
  });
  new ResizeObserver(() => {
    if (inspecting) frameInspectionViewport();
  }).observe(document.querySelector('#model-review'));
  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    frameInspectionViewport();
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    labelRenderer.setSize(window.innerWidth, window.innerHeight);
    routeMaterial.resolution.set(window.innerWidth, window.innerHeight);
  });

  // Load the generated local asset. Keep the OSM extrusion as a fallback until
  // both the model and its placement metadata have loaded successfully.
  Promise.all([
    new GLTFLoader().loadAsync('/models/heritage-hall.glb'),
    fetch('/models/heritage-hall.json').then(response => {
      if (!response.ok) throw new Error(`Model metadata returned HTTP ${response.status}`);
      return response.json();
    }),
  ]).then(([gltf, metadata]) => {
    if (!heritageBuilding || metadata.osmWayId !== HERITAGE_ID ||
        ![metadata.origin?.x, metadata.origin?.z].every(Number.isFinite) ||
        Math.hypot(metadata.origin.x - heritageBuilding.userData.centre.x,
          metadata.origin.z - heritageBuilding.userData.centre.z) > 0.1) {
      throw new Error('Heritage model placement does not match the local OSM footprint.');
    }
    heritageModel = gltf.scene;
    heritageModel.name = 'Heritage Hall | reference-backed exterior detail';
    heritageModel.position.set(metadata.origin.x, 0, metadata.origin.z);
    let meshCount = 0;
    heritageModel.traverse(object => {
      if (!object.isMesh) return;
      meshCount++;
      object.castShadow = true;
      object.receiveShadow = true;
      object.material = object.material.clone();
      object.material.envMapIntensity = /glazing|glass/i.test(object.material.name) ? 0.55 : 0.16;
    });
    if (!meshCount) throw new Error('Heritage GLB contains no renderable meshes.');
    heritageBuilding.geometry.dispose();
    heritageBuilding.geometry = new THREE.BufferGeometry();
    for (const child of [...heritageBuilding.children]) {
      if (child.isLineSegments) {
        heritageBuilding.remove(child);
        child.geometry.dispose();
      }
      if (child.isCSS2DObject) child.position.y = 23;
    }
    heritageBuilding.add(heritageModel);
    heritageBuilding.userData.modelStage = metadata.stage;
    campusView.heritageModel = heritageModel;
    campusView.modelMetadata = metadata;
    sun.position.set(metadata.origin.x - 85, 145, metadata.origin.z + 135);
    sun.target.position.set(metadata.origin.x, 0, metadata.origin.z + 30);
    scene.add(sun.target);
    Object.assign(sun.shadow.camera, { left: -155, right: 155, top: 155, bottom: -155, near: 1, far: 400 });
    sun.shadow.camera.updateProjectionMatrix();
    sun.shadow.mapSize.set(4096, 4096);
    sun.shadow.normalBias = 0.045;
    sun.shadow.bias = -0.0005;
    document.querySelector('#inspect-heritage').disabled = false;
    document.querySelector('#model-load-state').textContent = `${metadata.meshCount} editable part families · Blender detail source`;
    console.info('Heritage Hall exterior-detail model loaded', metadata);
    focusHeritage();
    if (metadata.site) {
      new GLTFLoader().loadAsync(metadata.site.asset).then(siteGLTF => {
        heritageSite = siteGLTF.scene;
        siteMetadata = metadata.site;
        // Repeated linked Blender tree meshes become GPU instances, grouped by
        // geometry and material. World matrices are captured before reparenting.
        heritageSite.updateMatrixWorld(true);
        const repeated = new Map();
        heritageSite.traverse(object => {
          if (!object.isMesh) return;
          object.castShadow = !/Ground|Lawn|OSM|Edge/.test(object.name);
          object.receiveShadow = true;
          const materials = Array.isArray(object.material) ? object.material : [object.material];
          for (const material of materials) material.envMapIntensity = /bronze/i.test(material.name) ? 0.65 : 0.16;
          let parent = object;
          let isTree = false;
          while (parent && parent !== heritageSite) {
            isTree ||= Boolean(parent.userData.tree_instance);
            parent = parent.parent;
          }
          if (!isTree) return;
          const key = object.geometry.uuid + materials.map(material => material.uuid).join(',');
          if (!repeated.has(key)) repeated.set(key, []);
          repeated.get(key).push(object);
        });
        for (const objects of repeated.values()) {
          if (objects.length < 2) continue;
          const instances = new THREE.InstancedMesh(objects[0].geometry, objects[0].material, objects.length);
          instances.name = 'Instanced precinct trees';
          objects.forEach((object, index) => {
            instances.setMatrixAt(index, object.matrixWorld);
            object.removeFromParent();
          });
          instances.castShadow = true;
          instances.receiveShadow = true;
          instances.computeBoundingSphere();
          heritageSite.add(instances);
        }
        heritageSite.position.set(metadata.origin.x, 0, metadata.origin.z);
        heritageSite.visible = surroundingsVisible;
        scene.add(heritageSite);
        campusView.heritageSite = heritageSite;
        document.querySelector('#toggle-surroundings').disabled = false;
        document.querySelectorAll('[data-model-view="site"], [data-model-view="sculpture"], [data-model-view="arrival"]').forEach(button => { button.disabled = false; });
        document.querySelector('#model-load-state').textContent = `${metadata.site.treeCount} trees · ${metadata.site.roadWays} road ways · ${metadata.site.pathWays} path ways · Local Blender scene`;
        console.info('Heritage precinct loaded', JSON.stringify({ ...metadata.site, treeInstanceBatches: repeated.size }));
        focusHeritage('site');
      }).catch(error => {
        console.error('Heritage surroundings failed to load:', error);
        document.querySelector('#model-load-state').textContent = 'Hall loaded; surroundings unavailable. Reload to retry.';
      });
    }
  }).catch(error => {
    console.error('Heritage Hall model failed to load:', error);
    document.querySelector('#status').textContent = 'Heritage model unavailable · Campus fallback';
    document.querySelector('#model-load-state').textContent = error.message;
    document.querySelector('#inspect-heritage').textContent = 'Model unavailable';
  });

  const renderedCount = buildingGroup.children.length;
  const excludedCount = buildings.filter(way => hasGeometry(way) && !isNearCampus(way)).length;
  document.querySelector('#building-count').textContent = renderedCount;
  document.querySelector('#path-count').textContent = campusPaths.length;
  document.querySelector('#data-note').textContent = `5 km Kampar filter · ${excludedCount} distant buildings excluded. Includes ${campusPaths.filter(way => way.geometry.length === 2).length} two-point path links. Heights use OSM levels, or 3 storeys by default.`;
  document.querySelector('#label-summary').textContent = `${buildingLabels.length} named buildings · Zoom in to see labels.`;
  document.querySelector('#status').textContent = walkwayGraph.connectedEnough
    ? 'Milestone 4 · Zoom in for labels'
    : 'Milestone 4 · Connectivity check failed';
  console.info('Milestone 4: building labels', {
    labelledBuildings: buildingLabels.length,
    unlabelledBuildings: renderedCount - buildingLabels.length,
    officialNameOverrides: buildingGroup.children.filter(building => Object.hasOwn(blockNames, building.userData.id)).length,
    distanceThresholdMetres: LABEL_DISTANCE,
  });
  console.info(`${renderedCount} buildings rendered; ${campusPaths.length} road/path ways drawn.`, {
    sourceBuildings: buildings.length,
    sourcePaths: paths.length,
    excludedDistantBuildings: excludedCount,
    skippedBuildingGeometry: buildings.length - excludedCount - renderedCount,
  });
  renderer.setAnimationLoop(time => {
    controls.update();
    if (marker.visible && navigation.route?.distance > 0) {
      // Accelerated demo animation: constant distance per frame, independent of node spacing.
      const travelled = (Math.max(0, time - animationStarted) / 1000 * 45) % navigation.route.distance;
      let segment = 1;
      while (segment < cumulativeDistances.length - 1 && cumulativeDistances[segment] <= travelled) segment++;
      const segmentLength = cumulativeDistances[segment] - cumulativeDistances[segment - 1];
      const fraction = segmentLength > 0 ? (travelled - cumulativeDistances[segment - 1]) / segmentLength : 0;
      marker.position.lerpVectors(routePoints[segment - 1], routePoints[segment], fraction);
    }
    renderer.render(scene, camera);
    for (const label of buildingLabels) {
      label.getWorldPosition(labelPosition);
      label.visible = !inspecting && camera.position.distanceToSquared(labelPosition) <= LABEL_DISTANCE * LABEL_DISTANCE;
    }
    labelRenderer.render(scene, camera);
  });
} catch (error) {
  console.error(error);
  document.querySelector('#status').textContent = 'Unable to render campus';
  const message = document.querySelector('#error');
  message.hidden = false;
  message.textContent = `Campus viewer could not start: ${error.message} Check that WebGL is available in your browser.`;
}
