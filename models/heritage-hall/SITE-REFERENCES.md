# Heritage Hall: exterior and immediate landscape

## Scope and evidence

This pass adds the immediate Heritage Hall precinct to the existing editable
building. It is a photograph-guided reconstruction, with documented estimates.
It is not a site survey, photogrammetric scan or exact replica of the sculpture.

References inspected for this pass on 13 September 2026:

- [UTAR: Bronze Sculptures of Confucius and Einstein](https://dccpr.utar.edu.my/universityicon_bronze_sculptures_confucius_einstein.php).
  The official description identifies the two seated scholars, their chessboard,
  and the location in front of Heritage Hall. It gives heights of 1.83 m and
  1.68 m, a 0.91 m square, 0.76 m high table, and a pedestal 8 m long and
  0.46 m high. The published pedestal width does not clearly describe the entire
  stepped surround visible in photographs; the model's platform depth is estimated.
- [Official wide sculpture photograph](https://dccpr.utar.edu.my/images/img100-01rvcopy_1557905624.jpg?n=1557905651437set).
  Used to examine the seated poses, bronze finish, cast block seats, pale stepped
  platform, sloping plaque, lawn and tree backdrop.
- [Confucius detail](https://dccpr.utar.edu.my/images/1557906782236rvcopy_1557906755.jpg?n=1557906782555set)
  and [Einstein detail](https://dccpr.utar.edu.my/images/1557906827710rvcopy_1557906801.jpg?n=1557906828049set).
  Used for robe, beard, hair, jacket, chin-resting pose and board-game forms.
- [UTAR Kampar virtual tour](https://about.utar.edu.my/virtual-tour/utar-kampar-campus/),
  Bronze Sculpture scene `panorama_DCF47363_CF80_614B_41E0_0DD7BAAE1AA3`.
  Inspected the four horizontal 512-pixel cube-face previews. They show the open
  lawn, access road between lawn and hall, three flagpoles, scattered front-lawn
  trees and dense perimeter planting. These are four directions at one viewpoint,
  not four independent site photographs. Panorama perspective is not a measurement.
- [UTAR frontage close-up](https://study.utar.edu.my/images/1571198375365rvcopy_1571198349.jpg?n=1571198375868set).
  Cross-checked the existing canopy, pale columns, glazing bands and entrance canopy.
- Local `src/data/campus.json`: road, parking-aisle and footpath centre-lines,
  building footprints and the original Heritage Hall placement.

Downloaded reference photographs remain in temporary research storage. They are
not shipped as textures. Surface maps and vegetation geometry are original,
procedurally generated assets. OSM attribution remains visible in the viewer.

## Modelled and estimated

The immediate precinct is approximately 279 × 247 m. Road and path alignments
come from the local OSM export, clipped to this boundary; most widths are estimates.
The main road uses its two-lane tag. Surface geometry retains the source paths'
access restrictions as source data; the renderer does not establish public access.
Parking envelopes and bay markings are interpretations between mapped aisles.

81 trees use three original broadleaf templates. Individual locations, species,
heights, crown shapes and shrub placement are estimates based on the overall
appearance of the photographs. Road/footpath clearances and building footprints
are checked before placing trees. Fine grass is concentrated around the sculpture.

The sculpture centre is provisionally placed 5 m west and 83 m south of the
building's footprint centre. Its orientation, approach-path alignment and stepped
platform depth remain estimates. Poses and garments are interpreted in geometry;
the faces, hands and drapery are simplified and should not be mistaken for the
original artist's exact forms. Only a short plaque title is modelled. The full
inscription and university emblem have not been transcribed or reproduced.

Three flagpoles follow the reference grouping. The cloth has simplified colour
motifs, including a Malaysian crescent and fourteen-point star. The small UTAR
logo is omitted. Lighting-fixture placement is an approximation.

The hall receives less uniform wall/roof surfaces and adjusted reflective glazing.
Fine standing seams follow the existing canopy surface; seam spacing is an
estimated material treatment. The original footprint and approved massing remain.
Unobserved rear elevations remain simplified; no unsupported windows or rooms
were introduced. See `REFERENCES.md` for the earlier building reference audit.

## Build and deliverables

Run from the project root:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python scripts/build_heritage_site.py
```

The script reads `heritage-hall-detail.blend`, which it does not overwrite. It writes:

- `heritage-hall-landscape.blend`: editable hall, landscape, linked trees, sculpture,
  materials, daylight rig and review camera.
- `public/models/heritage-hall.glb`: refined building, used by the campus viewer.
- `public/models/heritage-hall-site.glb`: separate surrounding landscape.
- `public/models/heritage-hall.json`: placement, stage and landscape counts.
- Nine PNG views: site, arrival, sculpture, elevated, front, rear, side, entrance,
  and facade.

Set `HERITAGE_DRAFT=1` for a smaller, lower-sample site render,
`HERITAGE_VIEWS=site,arrival,sculpture` to render selected views, or
`HERITAGE_NO_RENDER=1` to export and save without rendering. Running the earlier
`build_heritage.py` replaces the base building outputs; rerun this script afterward
to restore the landscape delivery. Save manual work under a separate filename;
this generator does not ingest edits to its own output file.

Blender uses X east, Y north and Z up. Both GLBs export Y up and share the same
local origin. The browser places the landscape separately from the clickable
hall; selecting grass or a tree therefore does not select the hall for routing.
Repeated tree meshes become Three.js InstancedMesh groups on load. Blender bump
nodes enhance offline renders; the portable browser materials use the packed
albedo maps and physical material parameters. The two renderers will differ.

The earlier elevated/front PNGs are preserved in `before-landscape/` for comparison.

## Verification

- Both exported assets have finite position coordinates and are below the
  generator's 40 MB per-asset guard. The landscape is approximately 9 MB.
- The browser confirms 81 trees in 15 GPU instance groups. Site geometry stays
  separate from building picking. A rendered campus-overview click selected
  Heritage Hall, then successfully routed to Medical Centre (1,272 m displayed).
- The existing Heritage Hall to Faculty of Science graph regression returns
  645.0515748577889 m across 39 route nodes; the 1,632-node graph is unchanged.
- The landscape, arrival and sculpture views, panel collapse and campus overview
  were inspected in the browser. Sculpture framing and panel collapse were also
  checked at 390 × 844; the viewport was restored afterward.
- Iterative render review corrected coplanar road-join artifacts, excessive
  surface repetition, an obstructed arrival camera, and a local-scale remesh
  problem before final delivery.
- The final exported files are approximately 3.4 MB and 9.3 MB, with finite
  vertex coordinates. Nine render views were inspected across the passes, including
  the corrected sculpture platform and plaque. Final browser loading reports no
  console errors; the surroundings visibility toggle works. Production build
  passes with Vite's existing JavaScript bundle-size advisory.
