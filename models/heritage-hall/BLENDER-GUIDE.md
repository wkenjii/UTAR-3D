# Open and inspect Heritage Hall in Blender

## Current landscape delivery

Open **`heritage-hall-landscape.blend`** for the latest hall, surrounding roads,
walkpaths, planting and Confucius–Einstein sculpture. The older detail file below
is retained as the source building snapshot.

In the Outliner, expand **LANDSCAPE | Heritage Hall precinct** for the sculpture,
roads and linked tree instances. The building stays in its architectural
collections. **RENDER ONLY | Daylight cameras** contains the presentation rig.
The file opens with a view of the complete precinct. Material Preview shows the
model interactively; Rendered shading or F12 uses the saved Cycles daylight rig.

In the browser, select **Landscape**, **Arrival** or **Sculpture**. Use
**Hide surroundings** to isolate the building and **Hide info** to reclaim screen
space. Drag to orbit, right-drag to pan and scroll/pinch to inspect smaller details.

`scripts/build_heritage_site.py` regenerates this landscape master and browser
assets from `heritage-hall-detail.blend`. Save manual edits in a separate file.
See `SITE-REFERENCES.md` for reference sources and estimated features.

## Open the editable model

The current model is:

`models/heritage-hall/heritage-hall-detail.blend`

In Finder, press **Command–Shift–G** and paste:

```
/Users/User/Documents/GPT-Astra-Project/models/heritage-hall/
```

Open `heritage-hall-detail.blend` with Blender. Alternatively, in Blender choose
**File → Open**, navigate to this folder and open that file. A `.blend` file is
opened directly; you do not need to import the browser `.glb` asset.

The older `heritage-hall.blend` is the approved first shape pass.

## Inspect without needing a numeric keypad

- **Orbit:** drag the coloured XYZ navigation gizmo at the top-right of the 3D
  viewport. With a three-button mouse, hold and drag the middle button.
- **Zoom:** scroll over the viewport, or drag its magnifying-glass icon.
- **Pan:** drag the hand navigation icon, or Shift + middle-mouse drag.
- **Recover the view:** choose **View → Frame All** in the viewport menu.
- **See materials:** click **Material Preview**, the third of the four shading
  spheres at the upper-right. This mode is already saved in the file.
- **See the prepared render view:** choose **View → Cameras → Active Camera**.
- **Render an image:** choose **Render → Render Image**. The supplied scene has
  a camera, studio ground and lighting; those are hidden only in the viewport.

The image panels in `public/previews/` are already rendered, including close-up
entrance and façade views, so you can inspect those without waiting for a render.

## Find the building parts

Expand **HERITAGE HALL | Exterior detail study** in the Outliner (top-right).
Its six collections separate massing, primary frontage, canopy/columns,
glazing/cladding, soffit details and the entrance assembly. Their eye icons
temporarily hide or show parts. Repeated small elements such as mullions are
combined into editable mesh families to keep the browser model efficient.

## Save your own edits

Use **File → Save As** to create a separate file such as
`heritage-hall-my-edits.blend` before manually modifying the model. Running
`scripts/build_heritage.py` regenerates `heritage-hall-detail.blend` and the GLB;
it does not incorporate manual edits automatically.

## Review in the browser

Open **http://localhost:5173/** while the Vite server is running (`npm run dev`
from the project root). The viewer starts in Heritage Hall inspection mode.

- Choose **Entrance detail** for the door, projecting canopy and paving, or
  **Façade detail** for glazing, cladding and upper screening.
- **Perspective**, **Front**, **Side** and **Rear** show the whole building.
- Use **Hide info / Show info** beside the title to collapse or reopen the panel.
  The camera keeps the model centred in the available review area. Resizing the
  window preserves your orbit and relative zoom.
- Drag to orbit and scroll/pinch to zoom closer. **Reset view** returns to the
  selected preset. On a small screen, scroll inside the panel for notes and links.
- Use **360° auto-rotate** for a continuous exterior review. Selecting a preset
  stops the rotation.
- The six **Blender preview renders** links open the prepared PNGs.
- **Campus overview** returns to the map and routing controls. **Inspect Heritage
  Hall** returns to the model.

## Model status

Front details are based on public photographic evidence, with estimated sizes.
The rear/side elevations remain simplified where references are missing. Read
`REFERENCES.md` for the source list and the observed-versus-estimated breakdown.
The exterior-detail milestone is verified and ready for user visual review.
