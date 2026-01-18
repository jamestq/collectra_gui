/**
 * Collectra + Annotorious Main Entry Point
 *
 * Orchestrates the entire annotation system:
 * - Loads Collectra YAML data
 * - Initializes Annotorious for bounding box editing
 * - Renders text data table
 * - Manages bidirectional selection between annotations and table
 * - Handles data persistence
 */

import { loadCollectra, normalizeToArray } from './io/loadCollectra.js';
import { saveCollectra, downloadYaml } from './io/saveCollectra.js';
import { initAnnotorious, loadAnnotations } from './annotorious/setup.js';
import { setupHandlers, createParentContext } from './annotorious/handlers.js';
import { yamlToAnnotorious } from './converter/yamlToAnnotorious.js';
import { annotoriousToYaml } from './converter/annotoriousToYaml.js';
import { createIndexManager } from './state/parentIndex.js';
import { createSelectionManager, wireAnnotoriousEvents } from './state/selectionManager.js';
import { renderTextTable, highlightRows, clearHighlights } from './ui/textTable.js';
import { createTableHandlers } from './ui/tableHandlers.js';

/**
 * Main application state.
 */
let app = {
  yamlData: null,
  anno: null,
  indexManager: null,
  selectionManager: null,
  parentContext: null,
  collectraPath: null,
  cleanupFunctions: []
};

/**
 * Initialize and load the Collectra annotation system.
 *
 * @param {string} collectraPath - Path to .collectra folder or URL
 * @param {Object} [options={}] - Configuration options
 * @param {string} [options.imageElementId='annotationImage'] - ID of image element
 * @param {string} [options.tableElementId='textDataTable'] - ID of table element
 * @param {string} [options.defaultParent] - Default parent ID for new annotations
 * @returns {Promise<void>}
 */
export async function initApp(collectraPath, options = {}) {
  const {
    imageElementId = 'annotationImage',
    tableElementId = 'textDataTable',
    defaultParent = null
  } = options;

  try {
    // Show loading state
    showLoading();

    // Store path
    app.collectraPath = collectraPath;

    // Load YAML data
    console.log('Loading Collectra data from:', collectraPath);
    app.yamlData = await loadCollectra(collectraPath);
    console.log('Loaded YAML data:', app.yamlData);

    // Get image source
    if (!app.yamlData.root_image_label || !app.yamlData.root_image_label.data) {
      throw new Error('No root_image_label.data found in YAML');
    }

    const imageSource = app.yamlData.root_image_label.data;

    // Set image source
    const imageElement = document.getElementById(imageElementId);
    if (!imageElement) {
      throw new Error(`Image element not found: #${imageElementId}`);
    }

    imageElement.src = imageSource;

    // Wait for image to load before initializing Annotorious
    await new Promise((resolve, reject) => {
      imageElement.onload = resolve;
      imageElement.onerror = () => reject(new Error(`Failed to load image: ${imageSource}`));
    });

    // Initialize Annotorious
    console.log('Initializing Annotorious...');
    app.anno = initAnnotorious(imageElement);

    // Build parent index
    app.indexManager = createIndexManager(app.yamlData);

    // Create selection manager
    app.selectionManager = createSelectionManager({ anno: app.anno });

    // Create parent context for new annotations
    app.parentContext = createParentContext(
      defaultParent || app.yamlData.root_image_label?.id
    );

    // Load annotations into Annotorious
    loadAnnotationsFromYaml();

    // Setup Annotorious event handlers
    const handlersCleanup = setupHandlers(
      app.anno,
      handleAnnotationChange,
      { getParents: () => app.parentContext.getParents() }
    );
    app.cleanupFunctions.push(handlersCleanup);

    // Wire Annotorious selection events
    const selectionCleanup = wireAnnotoriousEvents(
      app.anno,
      app.selectionManager,
      app.indexManager,
      {
        onHighlightTableRows: (ids) => highlightRows(ids),
        onHighlightAnnotations: (ids) => console.log('Highlight annotations:', ids)
      }
    );
    app.cleanupFunctions.push(selectionCleanup);

    // Render text table
    renderTable();

    // Hide loading state
    hideLoading();

    console.log('Application initialized successfully');
  } catch (err) {
    console.error('Failed to initialize application:', err);
    showError(err.message);
  }
}

/**
 * Load annotations from YAML data into Annotorious.
 */
function loadAnnotationsFromYaml() {
  const annotationTypes = [
    'cropped_image_inside_root_image',
    'sub_cropped_image'
  ];

  const imageSource = app.yamlData.root_image_label.data;
  const annotations = [];

  for (const type of annotationTypes) {
    const entries = normalizeToArray(app.yamlData[type]);
    for (const entry of entries) {
      try {
        const annotation = yamlToAnnotorious(entry, imageSource);
        annotations.push(annotation);
      } catch (err) {
        console.warn(`Failed to convert ${type} entry:`, entry, err);
      }
    }
  }

  console.log('Loading annotations:', annotations.length);
  loadAnnotations(app.anno, annotations);
}

/**
 * Handle annotation changes from Annotorious.
 *
 * @param {Object} change - Annotation change event
 * @param {string} change.type - 'create' | 'update' | 'delete'
 * @param {*} change.data - Change data
 */
function handleAnnotationChange(change) {
  console.log('Annotation change:', change);

  const { type, data } = change;

  switch (type) {
    case 'create':
      handleAnnotationCreate(data);
      break;
    case 'update':
      handleAnnotationUpdate(data);
      break;
    case 'delete':
      handleAnnotationDelete(data);
      break;
  }

  // Rebuild index and re-render
  onDataChange();
}

/**
 * Handle annotation creation.
 *
 * @param {Object} yamlEntry - New annotation in YAML format
 */
function handleAnnotationCreate(yamlEntry) {
  // Determine which type to add to based on parent depth
  // For simplicity, add to sub_cropped_image if it has parents, otherwise cropped_image_inside_root_image
  const hasParents = yamlEntry.parents && yamlEntry.parents.length > 0;
  const targetType = hasParents ? 'sub_cropped_image' : 'cropped_image_inside_root_image';

  // Add to YAML data
  if (!app.yamlData[targetType]) {
    app.yamlData[targetType] = [];
  } else if (!Array.isArray(app.yamlData[targetType])) {
    app.yamlData[targetType] = [app.yamlData[targetType]];
  }

  app.yamlData[targetType].push(yamlEntry);
  console.log(`Created annotation in ${targetType}:`, yamlEntry);
}

/**
 * Handle annotation update.
 *
 * @param {Object} yamlEntry - Updated annotation in YAML format
 */
function handleAnnotationUpdate(yamlEntry) {
  const annotationId = yamlEntry.id;

  // Find and update in either type
  const types = ['cropped_image_inside_root_image', 'sub_cropped_image'];
  let found = false;

  for (const type of types) {
    if (!app.yamlData[type]) continue;

    const entries = normalizeToArray(app.yamlData[type]);
    const index = entries.findIndex(e => String(e.id) === String(annotationId));

    if (index !== -1) {
      entries[index] = yamlEntry;
      app.yamlData[type] = entries.length === 1 ? entries[0] : entries;
      found = true;
      console.log(`Updated annotation in ${type}:`, yamlEntry);
      break;
    }
  }

  if (!found) {
    console.warn(`Annotation not found for update: ${annotationId}`);
  }
}

/**
 * Handle annotation deletion.
 *
 * @param {string} annotationId - ID of deleted annotation
 */
function handleAnnotationDelete(annotationId) {
  const types = ['cropped_image_inside_root_image', 'sub_cropped_image'];
  let found = false;

  for (const type of types) {
    if (!app.yamlData[type]) continue;

    const entries = normalizeToArray(app.yamlData[type]);
    const newEntries = entries.filter(e => String(e.id) !== String(annotationId));

    if (newEntries.length !== entries.length) {
      app.yamlData[type] = newEntries.length === 0 ? null :
                           newEntries.length === 1 ? newEntries[0] :
                           newEntries;
      found = true;
      console.log(`Deleted annotation from ${type}:`, annotationId);
      break;
    }
  }

  if (!found) {
    console.warn(`Annotation not found for deletion: ${annotationId}`);
  }
}

/**
 * Callback when YAML data changes.
 * Rebuilds indexes and re-renders UI.
 */
function onDataChange() {
  // Rebuild parent index
  app.indexManager.rebuild(app.yamlData);

  // Re-render table
  renderTable();

  // Mark as unsaved
  markUnsaved();
}

/**
 * Render the text table.
 */
function renderTable() {
  const handlers = createTableHandlers({
    yamlData: app.yamlData,
    indexManager: app.indexManager,
    selectionManager: app.selectionManager,
    anno: app.anno,
    onDataChange
  });

  renderTextTable(app.yamlData, app.indexManager, handlers);
}

/**
 * Save current YAML data.
 *
 * @returns {Promise<string>} YAML content
 */
export async function saveData() {
  try {
    const yamlContent = await saveCollectra(app.collectraPath, app.yamlData);
    console.log('Saved YAML data');
    markSaved();
    return yamlContent;
  } catch (err) {
    console.error('Failed to save:', err);
    showError(`Save failed: ${err.message}`);
    throw err;
  }
}

/**
 * Download YAML data as file.
 */
export async function downloadData() {
  try {
    const yamlContent = await saveCollectra(app.collectraPath, app.yamlData);
    downloadYaml(yamlContent, 'results.yaml');
    markSaved();
    console.log('Downloaded YAML data');
  } catch (err) {
    console.error('Failed to download:', err);
    showError(`Download failed: ${err.message}`);
  }
}

/**
 * Get current YAML data.
 *
 * @returns {Object} Current YAML data
 */
export function getData() {
  return app.yamlData;
}

/**
 * Cleanup and destroy the application.
 */
export function cleanup() {
  // Run all cleanup functions
  for (const cleanupFn of app.cleanupFunctions) {
    try {
      cleanupFn();
    } catch (err) {
      console.error('Cleanup error:', err);
    }
  }

  // Destroy Annotorious
  if (app.anno && app.anno.destroy) {
    app.anno.destroy();
  }

  // Clear state
  app = {
    yamlData: null,
    anno: null,
    indexManager: null,
    selectionManager: null,
    parentContext: null,
    collectraPath: null,
    cleanupFunctions: []
  };
}

/**
 * UI helper functions.
 */
function showLoading() {
  const el = document.getElementById('loadingIndicator');
  if (el) el.style.display = 'block';
}

function hideLoading() {
  const el = document.getElementById('loadingIndicator');
  if (el) el.style.display = 'none';
}

function showError(message) {
  const el = document.getElementById('errorMessage');
  if (el) {
    el.textContent = message;
    el.style.display = 'block';
  } else {
    alert(`Error: ${message}`);
  }
}

function markUnsaved() {
  const el = document.getElementById('saveStatus');
  if (el) {
    el.textContent = 'Unsaved changes';
    el.className = 'unsaved';
  }
}

function markSaved() {
  const el = document.getElementById('saveStatus');
  if (el) {
    el.textContent = 'All changes saved';
    el.className = 'saved';
  }
}

// Export main API
export default {
  initApp,
  saveData,
  downloadData,
  getData,
  cleanup
};
