# Build plan

## Current milestone — exterior realism and immediate surroundings

The user approved continuation on 13 September 2026 and explicitly requested
trees, roads, walkpaths and the sculpture in front of Heritage Hall. This extends
the earlier building-only scope to the surrounding precinct.

- [x] Inspect official sculpture photographs, dimensions and the four horizontal
  Bronze Sculpture tour previews; record source links and uncertainty.
- [x] Generate a separate editable landscape master, preserving the detail source.
  Add 81 trees, 20 OSM road ways, 21 path ways, parking envelopes, flagpoles,
  stepped sculpture platform and interpreted Confucius/Einstein figures.
- [x] Refine wall, roof and glazing materials and add canopy seam treatment.
- [x] Integrate a separate site GLB, instanced trees, landscape/arrival/sculpture
  views and a surroundings visibility toggle.
- [x] Finish final render review, asset validation and production build.
  Nine review views generated and inspected across the render passes. Final
  browser load has no console errors. Site visibility, mobile framing, building
  picking and route selection pass. `npm run build` passes with the existing
  JavaScript bundle-size advisory; final `dist/` is approximately 34 MB.

Current outputs and evidence are documented in
`models/heritage-hall/SITE-REFERENCES.md`. This delivery covers the immediate
Heritage Hall precinct; other campus buildings remain footprint models.

---

## Active plan — Heritage Hall modelling (user-approved)

The user has superseded the landscape-first ordering below. Start with a
reference-backed exterior model of Heritage Hall (OSM way 403039202).

- [x] **Shape-review milestone:** audit public references, generate an editable
  Blender model and local GLB, provide front/rear/side/elevated renders, and
  integrate close-up inspection into the current campus viewer. Document
  estimated dimensions and missing views. Stop for user review.
- [x] **Exterior detail milestone:** shape approved by user; refine photograph-backed
  glazing, cladding, soffits and entrance details, then open the editable model
  in local Blender and provide inspection instructions.
- [ ] After visual approval: expand to another building.

Shape-review output verified in Chrome: local GLB replaces the extrusion at the
original footprint; front/rear/side/perspective views, auto-rotation, preview
links and campus overview work. Existing Heritage Hall ↔ Faculty of Science
routing still returns about 645 m. Model geometry is finite and correctly Y-up.
User approved the proportions and requested detailed refinement using additional
public references. The exterior detail milestone is now complete for visual review.

Detail-pass verification: 65 editable Blender objects in six architectural
collections; 66 browser meshes and 33,966 finite exported vertex records. The
local GLB, all six inspection views and preview renders, auto-rotation, imported
model picking and the 645.05 m Heritage Hall ↔ Faculty of Science route passed.
The review panel can now collapse, entrance/façade presets frame more closely,
and camera framing accounts for the panel and toolbar on desktop, portrait and
landscape screens. Resizing retains the current orbit and relative zoom. No
external runtime requests or browser errors were observed; `npm run build` passed.

Opened `models/heritage-hall/heritage-hall-detail.blend` in local Blender and
updated `models/heritage-hall/BLENDER-GUIDE.md` with browser inspection steps.
**Stop here: await user visual approval before modelling another building.**

Existing implementation: campus footprints, graph, A* routes and CSS2D labels.
The original checklist below is retained as historical context; its landscape
steps and additional features are deferred.

---

Work through these in order. Do **one step at a time**, then stop and report.
Do not start the next step until asked.

Tick a box only when its "done when" is visibly true in the browser — not
when the code looks right.

Read `CLAUDE.md` first; it holds the constraints and conventions that apply
to every step here.

---

## [ ] 1. Empty world

Set up the four pieces that every 3D scene needs: a scene (the container), a
camera (where you're looking from), a renderer (the thing that paints pixels
into a canvas on the page), and OrbitControls (drag the mouse to orbit).

Then start the animation loop — the renderer draws a single picture each time
it's called, so it has to be called repeatedly, about sixty times a second,
forever.

Camera near/far: roughly 1 and 5000. Far too small and distant buildings get
clipped away.

**Done when:** a coloured rectangle fills the browser window and dragging the
mouse throws no console errors. Nothing appears to move — that's correct,
there's nothing in the world yet.

**Usual failure:** black screen with no errors. Almost always the animation
loop never started, or the canvas has zero height because its CSS parent
collapsed.

---

## [ ] 2. Ground plane

One large flat plane at y = 0, dark neutral colour, lying horizontal.

This exists to prove step 1 works. Until there's something in the world, you
can't tell whether the camera is moving.

**Done when:** dragging the mouse visibly orbits around a flat surface.

---

## [ ] 3. One single building

Not all of them. One.

Load `campus.json`, take the first way tagged `building`, project its corners
to metres, build a shape from them, extrude it upward, add it to the scene.

This is the step that proves the entire pipeline — file loading, projection,
geometry, material, scene. Everything after it is repetition.

**Done when:** one box sits on the ground plane at a believable size, roughly
10–50 metres across and taller than it is wide only if it genuinely is.

**Usual failures:**
- Nothing appears → the shape was built in the wrong plane, or the extrusion
  wasn't rotated flat
- A building the size of a continent → lat/lon fed in as degrees without
  converting to metres
- A building at the far edge of the world → `LAT0`/`LON0` don't match the
  actual campus centre

---

## [ ] 4. All buildings

Wrap step 3 in a loop over every way tagged `building`. Skip any with fewer
than 3 geometry points.

Frame the camera on the whole extent so the campus fits on screen.

**Done when:** a recognisable campus layout is visible. Report the number of
buildings rendered — it should be close to 149.

---

## [ ] 5. Water

Lake and waterway polygons, rendered flat (no extrusion), dark teal, slightly
shiny. Place at y = 0.2 per the render-order table in `CLAUDE.md`.

The lakes define what UTAR Kampar looks like. This is the step where the model
stops being generic.

**Done when:** Lake 18, Lake 19 and the surrounding water read clearly, with
no flickering where water meets ground.

**Usual failure:** flickering stripes = z-fighting, two surfaces at the same
height. Fix by separating the y-offsets, not by nudging the camera.

---

## [ ] 6. Ground cover

Landuse and leisure polygons — grass, woodland, recreation areas — flat, at
y = 0.1, in muted greens. Vary the shade slightly by tag so it isn't one
uniform slab.

**Done when:** the space between buildings reads as landscape rather than
empty floor.

---

## [ ] 7. Trees

A cone plus a short cylinder, placed at every `natural=tree` node, with small
random variation in scale and rotation so they don't look stamped.

There may be thousands. Use a single `InstancedMesh` — one mesh per tree will
tank the framerate.

**Done when:** trees are visible and the scene still runs smoothly. Report the
tree count and the framerate.

---

## [ ] 8. Lighting and mood

- One warm DirectionalLight, low in the sky, `castShadow` enabled
- One cool HemisphereLight for fill, so shadows aren't pure black
- Fog in a warm grey, with the scene background set to the same colour

This step changes the look more than steps 5–7 combined. Expect to sit and
adjust numbers until it feels right; that's the work, not a sign of being
stuck.

**Done when:** buildings cast soft shadows, distance softens into haze, and
the whole thing looks deliberate rather than unfinished.

---

## Later (do not start unless steps 1–8 are complete)

- Building labels from `blockNames.js`, as screen-space overlays that hide
  beyond a distance threshold
- Walking routes: build a graph from the `highway` ways, then A* between two
  clicked buildings. Two path ways connect only if they share a node — use
  the OSM node IDs as graph keys, or snap coordinates to 0.1 m buckets. Get
  this wrong and you get 718 disconnected segments and silent failure.
- Isochrones: Dijkstra outward from a building, colour every path node by
  walking distance. 5 minutes ≈ 420 m at 1.4 m/s.
- First-person walk mode, camera at 1.7 m, movement constrained to paths
