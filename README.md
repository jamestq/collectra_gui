# Collectra + Annotorious Annotation System

Browser-based annotation editor for Collectra YAML format using Annotorious for bounding box interaction.

## Features

- **Bounding Box Editing**: Draw, resize, move, and delete bounding boxes on images
- **Text Data Table**: View and edit text/text_draft entries with inline editing
- **Bidirectional Linking**: Click table rows to highlight linked boxes, click boxes to highlight linked text
- **YAML I/O**: Load from and save to Collectra YAML format
- **Parent-Child Relationships**: Maintains hierarchical relationships between annotations

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

## File Structure

```
├── src/
│   ├── converter/           # YAML ↔ W3C JSON conversion
│   │   ├── yamlToAnnotorious.js
│   │   ├── annotoriousToYaml.js
│   │   └── index.js
│   ├── annotorious/         # Annotorious setup and handlers
│   │   ├── setup.js
│   │   ├── handlers.js
│   │   └── index.js
│   ├── state/               # State management
│   │   ├── parentIndex.js
│   │   ├── selectionManager.js
│   │   └── index.js
│   ├── ui/                  # UI components
│   │   ├── textTable.js
│   │   ├── tableHandlers.js
│   │   └── index.js
│   ├── io/                  # I/O operations
│   │   ├── loadCollectra.js
│   │   ├── saveCollectra.js
│   │   └── index.js
│   └── index.js             # Main entry point
├── index.html               # Application layout
└── implementation_plan.md   # Detailed implementation plan
```

## Usage

### Running Locally

1. Serve the directory with a web server:
   ```bash
   python -m http.server 8000
   ```

2. Open in browser:
   ```
   http://localhost:8000/?path=./example.collectra
   ```

### Loading Data

Pass the Collectra folder path via URL parameter:
```
http://localhost:8000/?path=/path/to/folder.collectra
```

The system will load `results.yaml` from the specified folder.

### Editing Annotations

**Bounding Boxes:**
- Click image to create new annotation
- Drag corners to resize
- Drag box to move
- Press Delete or Backspace to remove selected box

**Text Entries:**
- Click table row to select and highlight linked boxes
- Click text cell to edit inline
- Press Enter or click outside to save changes
- Click Delete button to remove entry

### Saving Data

- Click "Download YAML" to save as `results.yaml`
- Modified data maintains Collectra format structure

## Coordinate Systems

### Collectra YAML Format
Center-based relative coordinates (0-1 range):
```yaml
x_center: 0.5        # X center as fraction of image width
y_center: 0.5        # Y center as fraction of image height
width_relative: 0.3  # Width as fraction of image width
height_relative: 0.2 # Height as fraction of image height
```

### Annotorious W3C Format
Top-left percentage coordinates (0-100 range):
```json
{
  "selector": {
    "value": "xywh=percent:35,40,30,20"
  }
}
```

## API

### Main API (`src/index.js`)

```javascript
import { initApp, saveData, downloadData, getData } from './src/index.js';

// Initialize with Collectra folder path
await initApp('./example.collectra', {
  imageElementId: 'annotationImage',
  tableElementId: 'textDataTable',
  defaultParent: 'root'
});

// Save current state
const yamlContent = await saveData();

// Download as file
await downloadData();

// Get current data
const data = getData();
```

### Conversion (`src/converter/`)

```javascript
import { yamlToAnnotorious, annotoriousToYaml } from './src/converter/index.js';

// YAML → W3C
const annotation = yamlToAnnotorious(yamlEntry, imageSource);

// W3C → YAML
const yamlEntry = annotoriousToYaml(annotation, parentIds);
```

### Parent Index (`src/state/parentIndex.js`)

```javascript
import { createIndexManager } from './src/state/parentIndex.js';

const indexManager = createIndexManager(yamlData);

// Query relationships
const children = indexManager.getChildren(parentId);
const parents = indexManager.getParents(childId);
const linkedTexts = indexManager.getLinkedTextEntries(boxId);
const linkedBoxes = indexManager.getLinkedBoundingBoxes(textId);
```

## Dependencies

- **@annotorious/annotorious** - Bounding box annotation UI (loaded via CDN)
- **js-yaml** - YAML parsing/serialization (loaded via CDN)

Both libraries are loaded via CDN in `index.html`.

## Browser Compatibility

Requires modern browser with:
- ES6 modules support
- Fetch API
- contenteditable
- CSS Grid

Tested in Chrome 90+, Firefox 88+, Safari 14+.

## Development

All modules use ES6 modules (import/export) and Google-style docstrings.

### Code Style
- Meaningful variable names
- Small focused functions
- Comprehensive error handling
- Google-style JSDoc comments

### Adding Features

1. Create new module in appropriate directory
2. Export via directory's `index.js`
3. Import in `src/index.js` main file
4. Wire up in `initApp()` function

## License

See project LICENSE file.
