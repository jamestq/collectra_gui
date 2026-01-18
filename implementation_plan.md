# Collectra + Annotorious Implementation Plan

## Overview

Implement an annotation system using the custom Collectra YAML format with Annotorious JS for bounding box interaction. A conversion layer translates between formats.

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Collectra      │     │  Conversion      │     │  Annotorious    │
│  YAML Format    │ ←─→ │  Layer           │ ←─→ │  W3C JSON       │
│  (storage)      │     │  (JS module)     │     │  (UI runtime)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                        ↕
                        ┌──────────────────┐     ┌─────────────────┐
                        │  Selection       │     │  Text Data      │
                        │  State Manager   │ ←─→ │  Table UI       │
                        └──────────────────┘     └─────────────────┘
```

## Features

- **Bounding box editing**: Annotorious provides resize, move, and delete out of the box
- **Text data table**: Displays text/text_draft entries with editable fields
- **Bidirectional linking**: Click table row → highlight bounding box; click bounding box → highlight table row

---

## Step 1: Set Up Project Structure

```
├── src/
│   ├── converter/
│   │   ├── yamlToAnnotorious.js    # YAML → W3C annotations
│   │   ├── annotoriousToYaml.js    # W3C → YAML format
│   │   └── index.js                # Export conversion utilities
│   ├── annotorious/
│   │   ├── setup.js                # Annotorious initialization
│   │   └── handlers.js             # Event handlers (create, update, delete)
│   ├── state/
│   │   ├── selectionManager.js     # Track selected annotation/text row
│   │   └── parentIndex.js          # Build parent→children lookup maps
│   ├── ui/
│   │   ├── textTable.js            # Render text data table
│   │   └── tableHandlers.js        # Table row click, edit, delete handlers
│   ├── io/
│   │   ├── loadCollectra.js        # Read .collectra folder, parse YAML
│   │   └── saveCollectra.js        # Write YAML back to folder
│   └── index.js                    # Main entry point
├── lib/
│   └── js-yaml.min.js              # YAML parsing library
└── index.html                      # Annotorious UI + text table layout
```

---

## Step 2: Implement YAML Parser/Writer

### Dependencies
- `js-yaml` for YAML parsing/serialization

### Tasks
- [ ] Create `loadCollectra(folderPath)` function
  - Read `results.yaml` from the collectra folder
  - Parse YAML to JavaScript object
  - Normalize single-parent values to arrays
- [ ] Create `saveCollectra(folderPath, data)` function
  - Serialize JavaScript object back to YAML
  - Write to `results.yaml`

---

## Step 3: Implement Conversion Layer

### 3a. YAML → Annotorious (for display)

```javascript
// src/converter/yamlToAnnotorious.js

function yamlToAnnotorious(yamlEntry, imageSource) {
  const { id, x_center, y_center, width_relative, height_relative } = yamlEntry;

  // Convert center-based relative coords to top-left percentage
  const x = (x_center - width_relative / 2) * 100;
  const y = (y_center - height_relative / 2) * 100;
  const w = width_relative * 100;
  const h = height_relative * 100;

  return {
    "@context": "http://www.w3.org/ns/anno.jsonld",
    "id": `#${id}`,
    "type": "Annotation",
    "body": [],
    "target": {
      "source": imageSource,
      "selector": {
        "type": "FragmentSelector",
        "conformsTo": "http://www.w3.org/TR/media-frags/",
        "value": `xywh=percent:${x},${y},${w},${h}`
      }
    }
  };
}
```

### 3b. Annotorious → YAML (for storage)

```javascript
// src/converter/annotoriousToYaml.js

function annotoriousToYaml(annotation, parents = []) {
  const selector = annotation.target.selector.value;
  // Parse "xywh=percent:x,y,w,h"
  const match = selector.match(/xywh=percent:([\d.]+),([\d.]+),([\d.]+),([\d.]+)/);
  const [, x, y, w, h] = match.map(Number);

  // Convert top-left percentage to center-based relative
  const width_relative = w / 100;
  const height_relative = h / 100;
  const x_center = (x / 100) + (width_relative / 2);
  const y_center = (y / 100) + (height_relative / 2);

  return {
    id: annotation.id.replace('#', ''),
    data: annotation.target.source,
    parents: parents.length === 1 ? parents[0] : parents,
    x_center,
    y_center,
    width_relative,
    height_relative
  };
}
```

### Tasks
- [ ] Implement `yamlToAnnotorious(yamlEntry, imageSource)`
- [ ] Implement `annotoriousToYaml(annotation, parents)`
- [ ] Handle edge cases (missing fields, invalid coordinates)
- [ ] Write unit tests for coordinate conversion accuracy

---

## Step 4: Annotorious Setup

### 4a. Initialize Annotorious

```javascript
// src/annotorious/setup.js

import { Annotorious } from '@annotorious/annotorious';

export function initAnnotorious(imageElement) {
  const anno = new Annotorious({
    image: imageElement,
    drawOnSingleClick: true,
    allowEmpty: false
  });

  return anno;
}
```

### 4b. Event Handlers

```javascript
// src/annotorious/handlers.js

export function setupHandlers(anno, onUpdate) {
  anno.on('createAnnotation', (annotation) => {
    // Convert to YAML format and add to data model
    const yamlEntry = annotoriousToYaml(annotation, [currentParentId]);
    onUpdate('create', yamlEntry);
  });

  anno.on('updateAnnotation', (annotation, previous) => {
    const yamlEntry = annotoriousToYaml(annotation, [currentParentId]);
    onUpdate('update', yamlEntry);
  });

  anno.on('deleteAnnotation', (annotation) => {
    onUpdate('delete', annotation.id);
  });
}
```

### Tasks
- [ ] Install Annotorious (`npm install @annotorious/annotorious`)
- [ ] Create initialization function
- [ ] Wire up create/update/delete event handlers
- [ ] Map handlers to update in-memory YAML structure

---

## Step 5: Load and Display Workflow

```javascript
// src/index.js

async function loadAndDisplay(collectraPath) {
  // 1. Load YAML
  const yamlData = await loadCollectra(collectraPath);

  // 2. Get image source
  const imageSource = yamlData.root_image_label.data;

  // 3. Initialize Annotorious on image
  const anno = initAnnotorious(document.getElementById('annotationImage'));

  // 4. Convert all bounding box entries to Annotorious format
  const annotationTypes = ['cropped_image_inside_root_image', 'sub_cropped_image'];

  for (const type of annotationTypes) {
    const entries = normalizeToArray(yamlData[type]);
    for (const entry of entries) {
      const annotation = yamlToAnnotorious(entry, imageSource);
      anno.addAnnotation(annotation);
    }
  }

  // 5. Set up handlers for edits
  setupHandlers(anno, handleAnnotationChange);
}

function normalizeToArray(value) {
  if (!value) return [];
  return Array.isArray(value) ? value : [value];
}
```

### Tasks
- [ ] Implement main load/display flow
- [ ] Create `normalizeToArray` utility
- [ ] Handle nested annotation types dynamically

---

## Step 6: Save Workflow

```javascript
async function saveCurrentState(collectraPath, yamlData) {
  await saveCollectra(collectraPath, yamlData);
}
```

### Tasks
- [ ] Implement save on user action (button or auto-save)
- [ ] Preserve fields not related to bounding boxes (orientation, text, metadata)
- [ ] Validate YAML structure before saving

---

## Step 7: Parent-Child Relationship Handling

### Considerations
- When creating a sub-annotation, track which parent annotation it belongs to
- UI needs a way to select "current parent context"
- Conversion layer must preserve parent references

### Tasks
- [ ] Add UI to select parent annotation context
- [ ] Pass parent ID to `annotoriousToYaml` on creation
- [ ] Display hierarchy visually (optional: different colors per depth)

---

## Step 8: Testing

### Unit Tests
- [ ] Coordinate conversion round-trip (YAML → W3C → YAML should match)
- [ ] Parent array normalization
- [ ] YAML parsing with various structures

### Integration Tests
- [ ] Load real collectra folder, display annotations
- [ ] Create annotation, save, reload, verify persistence
- [ ] Edit annotation, verify coordinates update correctly

---

## Step 9: Parent-Child Index Builder

Build lookup maps to trace relationships between bounding boxes and text entries.

```javascript
// src/state/parentIndex.js

export function buildParentIndex(yamlData) {
  const parentToChildren = {};  // parentId → [childIds]
  const childToParents = {};    // childId → [parentIds]

  const allEntries = [
    ...normalizeToArray(yamlData.cropped_image_inside_root_image),
    ...normalizeToArray(yamlData.sub_cropped_image),
    ...normalizeToArray(yamlData.text_draft),
    ...normalizeToArray(yamlData.text),
  ];

  for (const entry of allEntries) {
    const parents = normalizeToArray(entry.parents);
    childToParents[entry.id] = parents;

    for (const parentId of parents) {
      if (!parentToChildren[parentId]) {
        parentToChildren[parentId] = [];
      }
      parentToChildren[parentId].push(entry.id);
    }
  }

  return { parentToChildren, childToParents };
}

// Find all text entries linked to a bounding box (direct or via ancestors)
export function getLinkedTextEntries(boundingBoxId, index, yamlData) {
  const textEntries = [
    ...normalizeToArray(yamlData.text_draft),
    ...normalizeToArray(yamlData.text),
  ];

  return textEntries.filter(entry => {
    const parents = normalizeToArray(entry.parents);
    return parents.includes(boundingBoxId);
  });
}

// Find bounding boxes linked to a text entry
export function getLinkedBoundingBoxes(textEntryId, index, yamlData) {
  const parents = index.childToParents[textEntryId] || [];
  const boundingBoxTypes = ['cropped_image_inside_root_image', 'sub_cropped_image'];

  const allBoxes = boundingBoxTypes.flatMap(type =>
    normalizeToArray(yamlData[type])
  );

  return allBoxes.filter(box => parents.includes(box.id));
}
```

### Tasks
- [ ] Implement `buildParentIndex(yamlData)`
- [ ] Implement `getLinkedTextEntries(boundingBoxId, ...)`
- [ ] Implement `getLinkedBoundingBoxes(textEntryId, ...)`
- [ ] Rebuild index when annotations change

---

## Step 10: Text Data Table UI

Render a table showing text and text_draft entries with their linked bounding box info.

### HTML Structure

```html
<!-- In index.html -->
<div class="app-layout">
  <div class="image-panel">
    <img id="annotationImage" src="" />
  </div>
  <div class="table-panel">
    <table id="textDataTable">
      <thead>
        <tr>
          <th>ID</th>
          <th>Type</th>
          <th>Text</th>
          <th>Linked Boxes</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
</div>
```

### Table Renderer

```javascript
// src/ui/textTable.js

export function renderTextTable(yamlData, index, onRowClick, onTextEdit) {
  const tbody = document.querySelector('#textDataTable tbody');
  tbody.innerHTML = '';

  const textEntries = [
    ...normalizeToArray(yamlData.text_draft).map(e => ({ ...e, type: 'draft' })),
    ...normalizeToArray(yamlData.text).map(e => ({ ...e, type: 'final' })),
  ];

  for (const entry of textEntries) {
    const linkedBoxes = getLinkedBoundingBoxes(entry.id, index, yamlData);
    const row = document.createElement('tr');
    row.dataset.entryId = entry.id;

    row.innerHTML = `
      <td>${entry.id}</td>
      <td><span class="badge badge-${entry.type}">${entry.type}</span></td>
      <td contenteditable="true" class="editable-cell">${entry.data}</td>
      <td>${linkedBoxes.map(b => b.id).join(', ')}</td>
      <td><button class="btn-delete" data-id="${entry.id}">Delete</button></td>
    `;

    row.addEventListener('click', () => onRowClick(entry.id, linkedBoxes));

    const editableCell = row.querySelector('.editable-cell');
    editableCell.addEventListener('blur', (e) => {
      onTextEdit(entry.id, e.target.textContent);
    });

    tbody.appendChild(row);
  }
}
```

### Tasks
- [ ] Create table HTML structure in `index.html`
- [ ] Implement `renderTextTable()` function
- [ ] Add inline editing for text cells
- [ ] Add delete button functionality
- [ ] Style table with CSS (highlight selected row)

---

## Step 11: Bidirectional Selection Linking

### Selection State Manager

```javascript
// src/state/selectionManager.js

export function createSelectionManager(anno) {
  let selectedAnnotationId = null;
  let selectedTextEntryId = null;
  const listeners = [];

  return {
    // Called when bounding box is selected in Annotorious
    selectAnnotation(annotationId) {
      selectedAnnotationId = annotationId;
      selectedTextEntryId = null;
      this.notify('annotation', annotationId);
    },

    // Called when table row is clicked
    selectTextEntry(textEntryId) {
      selectedTextEntryId = textEntryId;
      selectedAnnotationId = null;
      this.notify('text', textEntryId);
    },

    onSelectionChange(callback) {
      listeners.push(callback);
    },

    notify(type, id) {
      listeners.forEach(cb => cb(type, id));
    },

    getSelectedAnnotation() { return selectedAnnotationId; },
    getSelectedTextEntry() { return selectedTextEntryId; },
  };
}
```

### Wiring It Together

```javascript
// In src/index.js

const selectionManager = createSelectionManager(anno);

// Annotorious → Table: highlight linked text rows
anno.on('selectAnnotation', (annotation) => {
  const boxId = annotation.id.replace('#', '');
  selectionManager.selectAnnotation(boxId);

  // Find and highlight linked text entries
  const linkedTexts = getLinkedTextEntries(boxId, index, yamlData);
  highlightTableRows(linkedTexts.map(t => t.id));
});

// Table → Annotorious: highlight linked bounding boxes
function onRowClick(textEntryId, linkedBoxes) {
  selectionManager.selectTextEntry(textEntryId);

  // Clear previous selection, highlight linked boxes
  anno.cancelSelected();
  for (const box of linkedBoxes) {
    anno.selectAnnotation(`#${box.id}`);
    // Or use custom highlight if multi-select not supported:
    // highlightAnnotation(anno, box.id);
  }
}

function highlightTableRows(entryIds) {
  document.querySelectorAll('#textDataTable tr').forEach(row => {
    row.classList.toggle('highlighted', entryIds.includes(row.dataset.entryId));
  });
}
```

### Visual Feedback CSS

```css
/* Highlighted table row when bounding box selected */
#textDataTable tr.highlighted {
  background-color: #fff3cd;
  border-left: 3px solid #ffc107;
}

/* Highlighted bounding box when table row selected */
.a9s-annotation.highlighted .a9s-inner {
  stroke: #ffc107 !important;
  stroke-width: 3px !important;
}
```

### Tasks
- [ ] Implement `createSelectionManager()`
- [ ] Wire Annotorious `selectAnnotation` event to highlight table rows
- [ ] Wire table row click to highlight bounding boxes in Annotorious
- [ ] Add CSS for visual highlight feedback
- [ ] Handle multi-parent scenarios (text linked to multiple boxes)

---

## Step 12: Edge Cases and Polish

- [ ] Handle missing/malformed YAML gracefully
- [ ] Validate coordinates are within 0-1 range
- [ ] Handle image loading errors
- [ ] Add loading states for async operations
- [ ] Clear highlights when clicking empty areas
- [ ] Handle orphaned text entries (parent box deleted)

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `@annotorious/annotorious` | Bounding box UI |
| `js-yaml` | YAML parse/serialize |

---

## Open Questions

1. **Multi-image support**: Does a single collectra folder ever contain multiple root images?
2. **Annotation types**: Should the UI distinguish between `cropped_image_inside_root_image` and `sub_cropped_image` visually (different colors)?
3. **Text creation**: Should users be able to create new text entries from the UI, or only edit existing ones?
4. **Box deletion cascade**: When a bounding box is deleted, what happens to its child text entries? Options:
   - Delete children automatically
   - Orphan them (remove parent reference)
   - Block deletion until children are removed
