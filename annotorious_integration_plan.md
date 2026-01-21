# Plan: Draw Annotations on Image Using Annotorious

## Overview
Integrate Annotorious to display ImageCrop annotations from YAML data as visual bounding boxes on images.

## Current State
- **index.html**: Loads Annotorious CDN but has broken ES6 imports (line 201-202); never initializes Annotorious
- **api.py**: PyWebView API serves YAML data and images as base64
- **lineage_display.py**: AnnotationGraph parses YAML, provides node access
- **Data format**: YAML uses center-based relative coordinates (0-1 range)

## Key Insight: Coordinate Conversion
YAML format (center-based, 0-1) must convert to W3C format (top-left, 0-100%):
```
x = (x_center - width_relative/2) * 100
y = (y_center - height_relative/2) * 100
w = width_relative * 100
h = height_relative * 100
```

---

## Implementation Steps

### Step 1: Fix Annotorious Import in index.html
**File:** `/workspace/collectra_gui/index.html`

Remove broken ES6 imports (lines 201-202). The CDN script exposes `Annotorious` globally.

### Step 2: Add API Method for ImageCrop Coordinates
**File:** `/workspace/collectra_gui/api.py`

Add `get_image_crops_for_annotorious()` method that returns ImageCrop nodes with:
- `id`, `x_center`, `y_center`, `width_relative`, `height_relative`, `displayValue`

### Step 3: Add JavaScript Functions in index.html
**File:** `/workspace/collectra_gui/index.html`

1. **Global variable**: `let anno = null;`

2. **`convertYamlToW3CAnnotation(nodeData)`**: Converts YAML coords to W3C format
   - Returns W3C annotation with FragmentSelector: `xywh=percent:x,y,w,h`

3. **`initAnnotorious()`**: Initialize Annotorious on image element
   - Destroy existing instance if present
   - Wait for image to load
   - Create annotator with `readOnly: true`
   - Set up selection event handler

4. **`loadAnnotationsIntoAnnotorious()`**: Fetch and load annotations
   - Call `get_image_crops_for_annotorious()` API
   - Convert all to W3C format
   - Call `anno.setAnnotations()`

5. **`selectRowInGrid(nodeId)`**: Select AG Grid row by node ID

### Step 4: Modify Existing Functions
**File:** `/workspace/collectra_gui/index.html`

1. **`displayImageFromPath()`**: Add `img.onload` callback to:
   - Call `initAnnotorious()`
   - Call `loadAnnotationsIntoAnnotorious()` if YAML loaded

2. **`loadYaml()`**: After successful load:
   - Call `loadAnnotationsIntoAnnotorious()` if Annotorious initialized

3. **`gridOptions`**: Add `onSelectionChanged` handler to:
   - Call `anno.setSelected(nodeId)` when row selected

### Step 5: Add CSS Styles
**File:** `/workspace/collectra_gui/index.html`

Add annotation styling for default, selected, and hover states.

---

## Files to Modify

| File | Changes |
|------|---------|
| `/workspace/collectra_gui/api.py` | Add `get_image_crops_for_annotorious()` method |
| `/workspace/collectra_gui/index.html` | Remove broken imports, add functions, modify existing functions, add CSS |

---

## Data Flow
```
YAML File → load_yaml() → AnnotationGraph
                              ↓
              get_image_crops_for_annotorious()
                              ↓
              convertYamlToW3CAnnotation() (JS)
                              ↓
              anno.setAnnotations() → Visual boxes on image
```

---

## Selection Sync
- Click annotation on image → `selectionChanged` event → `selectRowInGrid()` → highlight table row
- Click row in table → `onSelectionChanged` → `anno.setSelected()` → highlight annotation

---

## Verification
1. Open the app with `python -m collectra_gui.api`
2. Select a `.grapto` folder containing YAML and image
3. Verify annotations appear as rectangles on the image
4. Click an annotation → corresponding row highlights in grid
5. Click a grid row → corresponding annotation highlights on image
6. Verify coordinates are visually correct by comparing to known crop positions
