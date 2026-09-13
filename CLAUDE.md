# UTAR Kampar 3D Campus

A browser-based 3D model of the UTAR Kampar campus. The user has approved a
building-first, reference-backed Blender workflow, starting with Heritage Hall.
Prioritise architectural resemblance and close-up inspection before more features.
The original OSM-only landscape plan below is deferred.

## Non-negotiables

- **Never fetch Overpass at runtime.** All map data is already exported to
  `src/data/campus.json`. The public Overpass API rate-limits and goes down;
  a runtime fetch turns a working demo into a blank screen. Read the local
  file only.
- **No invented factual detail.** Use local OSM footprints and identified public
  photographic references. Explicitly document estimated modelling dimensions
  and unobserved elevations; do not describe the model as measured or exact.
- **Vanilla JS only.** No React, no react-three-fiber, no TypeScript, no test
  framework, no Docker. Vite + three, that's it.
- **No mapping libraries.** No proj4, no Leaflet, no Mapbox, no GeoJSON
  conversion step. The projection below is all this project needs.
- **Stop at milestones.** Do not run the whole plan end to end. Complete one
  milestone, report what happened, and wait.

## Stack

- Vite dev server (`npm run dev`, serves on :5173)
- `three` — imported from npm; `OrbitControls` from
  `three/examples/jsm/controls/OrbitControls.js`
- No backend, no database, no auth. Everything client-side.
- Keep application code compact. The user-approved Blender workflow additionally
  permits Python build scripts, editable .blend sources, GLB assets, preview
  renders, and reference documentation. Python is build-time only.

## The data

`src/data/campus.json` is raw Overpass API output:

```json
{
  "elements": [
    {
      "type": "way",
      "id": 403049605,
      "tags": { "building": "yes", "name": "Block P" },
      "nodes": [123, 124, 125],
      "geometry": [{ "lat": 4.3384, "lon": 101.1367 }]
    }
  ]
}
```

Verified contents of the current download:

- 148 building ways and 719 highway ways across multiple locations.
- Within the approved 5 km Kampar filter: 49 buildings and 345 highway ways.
- No nearby water/ground-cover features, and no tree nodes or relations.

What is **not** in this export:

- building interiors, floor plans, room numbers
- facades, textures, roof shapes, materials
- accurate building heights (`building:levels` is tagged on very few)

Building exteriors may now be modelled from identified photographic references.
Use UTAR's VR360 imagery as reference, not as redistributed textures. Interiors
and measured architectural accuracy are outside the current milestone.

## Coordinate projection

Latitude/longitude are angles on a globe; three.js wants metres on a plane.
The campus is under 1 km across, so a flat-earth approximation is accurate to
a few centimetres. Use this and nothing else:

```js
const LAT0 = 4.3385;   // campus centre — VERIFY against campus.json extent
const LON0 = 101.1370;
const M_PER_DEG_LAT = 110540;
const M_PER_DEG_LON = 111320 * Math.cos(LAT0 * Math.PI / 180);

const project = ({ lat, lon }) => ({
  x: (lon - LON0) * M_PER_DEG_LON,
  z: -(lat - LAT0) * M_PER_DEG_LAT,   // north is -Z, three.js convention
});
```

Y is up. Buildings extrude along +Y.

## Building extrusion

Default height where `building:levels` is absent:

```js
const floors = Number(tags["building:levels"]) || 3;
const height = floors * 3.5;
```

Use `THREE.Shape` + `ExtrudeGeometry` with `bevelEnabled: false`, then
`geometry.rotateX(-Math.PI / 2)` to lay the extrusion flat.

Skip any way whose `geometry` has fewer than 3 points.

If a building has `building:part` features sharing its footprint, render the
parts and drop the parent — rendering both double-extrudes it.

## Render order (y-offsets)

Coplanar surfaces at the same Y produce z-fighting, a flickering stripe
effect that makes the scene look broken. Stack them:

| layer        | y     |
|--------------|-------|
| ground plane | 0.0   |
| landuse      | 0.1   |
| water        | 0.2   |
| paths        | 0.4   |
| buildings    | 0.0 → height |

## Performance

Trees may number in the thousands. Use a single `InstancedMesh`, not one mesh
per tree. Same for any other repeated small object.

## Multipolygon relations

Lakes are often relations, not ways. Each member has a `role`: render `outer`
rings as the shape and `inner` rings as holes via `THREE.Path`. If this gets
fiddly, skip holes — a missing island is not noticeable.

## Known unknowns

- One POI in the export carries a Kuala Lumpur address (`Jalan Malinja`,
  postcode 53300), which is Sungai Long, not Kampar. The campus area query
  may be capturing both UTAR campuses. Worth verifying before trusting
  building counts.
- Most buildings have no `name` tag. Official block names are being added
  manually in `src/data/blockNames.js`, keyed by OSM way ID, sourced from
  UTAR's published campus map PDF. That PDF is UTAR's asset — reference only,
  never ship it as a texture or redistribute it.

## Attribution

Map data © OpenStreetMap contributors, available under the Open Database
License. Any public deployment must carry this credit visibly.
