# Heritage Hall — exterior detail study

The user approved the first shape pass and requested a reference-backed detail
pass. The original `heritage-hall.blend` remains as the approved shape snapshot;
the current editable model is **`heritage-hall-detail.blend`**.

## Additional research for the detail pass

Screened **64 candidate photographs**: 28 from UTAR's Kampar Campus page and
36 from UTAR Perak Campus Photography Society's public Flickr photostream.
Most show other buildings, people, scenery, or events and were excluded from
Heritage Hall modelling. These are screening counts, not 64 usable photographs
of Heritage Hall. English and Chinese-name searches also surfaced social-media
pages, but no additional reliable rear-elevation photograph was obtained.

Selected sources, in addition to the panoramas below:

1. [UTAR Kampar Campus page](https://study.utar.edu.my/Kampar-Campus.php),
   [frontage close-up](https://study.utar.edu.my/images/1571198375365rvcopy_1571198349.jpg?n=1571198375868set).
   Shows façade glazing divisions, contrasting horizontal bands, roof soffit
   members, pale solid flanks, slender columns and a small projecting glass
   entrance canopy. The published image is only 360 × 225; it does not resolve
   exact module counts or construction dimensions.
2. [“heritage hall”, UTAR Perak Campus Photography Society, S Guat Shan](https://www.flickr.com/photos/utar_pcps/2663436157/),
   dated 13 July 2008. An upward view beneath the overhang confirms panelled
   soffit, structural members and contrasting paving. The age of this photo
   means it is corroboration, not proof of current condition.
3. [UTAR Heritage Hall page](https://utar.edu.my/Heritage-Hall.php): confirms
   building identity and floor-based departmental uses. It contains no useful
   exterior photograph; department listings are not interpreted as floor plans.
4. Official VR360 Bronze Sculpture viewpoint: inspected **2048 px front and
   right cube faces** for façade proportions, upper glazing/screen bands,
   cladding, entrance canopy and the colonnade.
5. Official VR360 Entrance viewpoint: inspected **four 1024 px horizontal cube
   faces** for framing, door hardware, sheltered paving and visible structural
   details. These are views from one viewpoint, not four separate survey images.

Candidate contact sheets and full reference images remain in temporary research
storage. This repository records source links and interpretations; it does not
redistribute UTAR or Flickr photographs as model textures.

## Added detail and confidence

| Model feature | Evidence | Remaining estimate |
|---|---|---|
| Curtain-wall mullions, transoms and alternating bands | UTAR close-up + front panorama | Panel counts, widths, exact colours |
| Upper clerestory/screen strip | Front panorama | Horizontal/vertical subdivision |
| Solid-wall panel joints and edge bevels | Front photographs | Joint grid, depths and bevel size |
| Roof soffit members and panel divisions | UTAR close-up + titled Flickr image | Member cross-sections and spacing |
| Projecting framed glass entrance canopy | UTAR close-up + front panorama | Width, projection, support geometry |
| Central entrance framing, sidelights and pulls | Front/entrance panoramas | Exact exterior door configuration and dimensions |
| Entrance paving | Sheltered entrance and Flickr image | Apron extent and pattern placement are approximate |

Repeated fine elements are combined into named mesh families for browser
performance. The Blender file groups them into six architectural collections.
The original generated concrete texture adds subtle surface variation. Glass is
a reflective exterior approximation; it does not imply reconstructed rooms.
The browser uses a procedural sky for reflections, rather than site photography.

## Sources inspected

- Local `src/data/campus.json`, OSM way **403039202**, named Heritage Hall / 文遗堂.
  Tagged `building:levels=3`. The 20 distinct footprint vertices supply the
  placement and outline. East–west extent is about 93.90 m; north–south extent
  is about 69.94 m. These are bounding extents, not surveyed façade lengths.
- [UTAR Kampar VR360](https://about.utar.edu.my/virtual-tour/utar-kampar-campus/):
  **The Bronze Sculpture**, scene
  `panorama_DCF47363_CF80_614B_41E0_0DD7BAAE1AA3`.
  UTAR's description places the sculptures in front of Heritage Hall. Inspected
  all horizontal cube faces and a 1024 px right-face view of the building.
- Same tour: **Entrance**, scene
  `panorama_EBFDD6AB_F1D2_07C6_41E4_051AA6EFFEDB`, linked from that viewpoint.
  Shows the sheltered circulation area, circular columns, grey screening,
  glazed partitions, and a signed multipurpose-hall entrance.
- Same tour: **Division of Programme Promotion**, scene
  `panorama_5532CF37_5A08_63E3_41BC_DAF0DA4DD38F`. Interior reference inspected
  to establish context; no room reconstruction is included.
- Same tour: **UTAR Kampar Campus** and **Kampar (Perak)** aerial panoramas.
  These establish campus context but are too distant to measure this roof.

The tour's script identifies its generation date as 8 February 2024. That is
not necessarily the photography date. Visual references may predate changes.
Reference images were inspected in temporary working storage; they are not
packaged into the browser app or used as textures.

## Approved first-pass massing retained

- Broad, bowed frontage consistent with the south edge of the OSM outline.
- Large, shallow overhanging roof and a line of slender full-height columns.
- Pale grey solid façade flanks, central blue-grey glazing bands, and a deeply
  recessed ground-level entry.
- Stepped footprint, with a narrower middle and a rectangular rear wing.

## Estimates and unresolved details

This is a **reference-backed exterior study**, not a measured architectural reconstruction.
The front canopy height, crown/profile, overhang, column diameter/spacing,
glazing subdivision, cladding grid, entry-canopy dimensions and recess depth are visual estimates. The floor tag does
not establish the different volume heights. The script groups these estimates
in `ESTIMATES` so they can be corrected after review.

The rear and side elevations are not fully visible in the inspected references.
Their massing follows the footprint, but their walls remain deliberately plain.
Rear roof form, exact openings, structural layout, signage and all interiors
remain unresolved. No rooms or repeated windows have been added to the
unobserved elevations. Small front details are interpretations of photographic
evidence, not surveyed as-built records.

## Rebuild and review

From the project root:

```sh
"/Applications/Blender.app/Contents/MacOS/Blender" --background --python-exit-code 1 --python scripts/build_heritage.py
```

Outputs:

- `models/heritage-hall/heritage-hall-detail.blend` — current editable source.
- `models/heritage-hall/heritage-hall.blend` — retained approved shape snapshot.
- `public/models/heritage-hall.glb` — model-only asset, metres, Y-up on export.
- `public/models/heritage-hall.json` — placement and modelling-estimate metadata.
- `public/previews/heritage-hall-{front,rear,side,elevated,entrance,facade}.png` — generated renders.

Blender uses local X=east, Y=north, Z=up. The exporter converts this to glTF
X=east, Y=up, Z=south. The browser translates the model to the original OSM
footprint's bounding centre; it does not rescale it or extrude its parent again.

Review the new façade and entrance details against the linked sources.
Rear/side renders expose the unresolved massing rather than implying those
elevations are complete. See `BLENDER-GUIDE.md` for opening and inspection.

## Exterior-detail verification

Completed in Blender 5.2.1 LTS and Chrome:

- The editable file opens with **65 mesh objects in six architectural collections**,
  metric units, finite vertex coordinates and its original concrete texture packed.
- The GLB loads as **66 browser meshes with 33,966 exported vertex records**. The
  canopy's two materials split it into two renderable meshes. Coordinates are
  finite, Y-up and placed at the OSM bounding centre; the source extrusion is removed.
- Front, rear, side, elevated, entrance and façade browser views and their six
  local preview PNG links work. All six renders were visually inspected.
- Entrance and façade presets now frame more closely. Camera framing reserves
  space for the review panel and toolbar; the panel can be collapsed. Whole-model
  framing, panel toggling and resize were checked at 1440 × 1000, 390 × 844 and
  844 × 390. Orbit and relative zoom survive layout changes.
- Auto-rotation, campus overview, picking the imported model and the existing
  **645.05 m** Heritage Hall ↔ Faculty of Science graph route pass.
- The observed page reload uses local requests only, with no browser exceptions
  or console errors. `npm run build` passes (Vite reports a bundle-size advisory).
- Opened `heritage-hall-detail.blend` in local Blender for user inspection.

This completes the exterior-detail delivery milestone. Visual approval is still
pending; estimated dimensions and unresolved rear/side elevations remain as
documented above.

## Previous shape-pass verification

Generated with Blender 5.2.1. The browser loads 59 named mesh components with
2,110 exported vertex records. Their coordinates are finite; the model is Y-up,
rests at ground level and retains its metre scale and OSM placement. The original
Heritage Hall extrusion is removed only after the GLB loads successfully.

Chrome checks passed for all four inspection views, auto-rotation, generated
preview links, campus overview, picking the imported model and the existing
645.05 m graph route between Heritage Hall and Faculty of Science. Shadow-map
projection and bias were adjusted after visual review to remove roof banding.
