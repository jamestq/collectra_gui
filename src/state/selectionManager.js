/**
 * Selection State Manager
 *
 * Manages bidirectional selection state between Annotorious bounding boxes
 * and text table rows. Provides a pub/sub interface for selection changes.
 *
 * Selection flow:
 * - User clicks bounding box -> highlight linked text rows
 * - User clicks text row -> highlight linked bounding boxes
 */

/**
 * @typedef {'annotation' | 'text' | 'clear'} SelectionType
 */

/**
 * @typedef {Object} SelectionState
 * @property {string|null} annotationId - Currently selected annotation ID
 * @property {string|null} textEntryId - Currently selected text entry ID
 * @property {SelectionType} lastSelectionType - Type of the last selection
 */

/**
 * @typedef {function(SelectionType, string|null, SelectionState): void} SelectionListener
 */

/**
 * Create a selection manager for bidirectional linking.
 *
 * @param {Object} [options] - Configuration options
 * @param {Object} [options.anno] - Annotorious instance for programmatic selection
 * @returns {Object} Selection manager API
 */
export function createSelectionManager(options = {}) {
  const { anno = null } = options;

  /** @type {string|null} */
  let selectedAnnotationId = null;

  /** @type {string|null} */
  let selectedTextEntryId = null;

  /** @type {SelectionType} */
  let lastSelectionType = 'clear';

  /** @type {SelectionListener[]} */
  const listeners = [];

  /**
   * Get current selection state snapshot.
   * @returns {SelectionState}
   */
  function getState() {
    return {
      annotationId: selectedAnnotationId,
      textEntryId: selectedTextEntryId,
      lastSelectionType
    };
  }

  /**
   * Notify all listeners of a selection change.
   * @param {SelectionType} type - Type of selection
   * @param {string|null} id - Selected ID
   */
  function notify(type, id) {
    const state = getState();
    for (const listener of listeners) {
      try {
        listener(type, id, state);
      } catch (err) {
        console.error('Selection listener error:', err);
      }
    }
  }

  return {
    /**
     * Select an annotation (bounding box).
     * Called when user clicks a bounding box in Annotorious.
     *
     * @param {string} annotationId - ID of the selected annotation (without # prefix)
     */
    selectAnnotation(annotationId) {
      const id = annotationId ? String(annotationId).replace(/^#/, '') : null;
      selectedAnnotationId = id;
      selectedTextEntryId = null;
      lastSelectionType = 'annotation';
      notify('annotation', id);
    },

    /**
     * Select a text entry (table row).
     * Called when user clicks a row in the text table.
     *
     * @param {string} textEntryId - ID of the selected text entry
     */
    selectTextEntry(textEntryId) {
      const id = textEntryId ? String(textEntryId) : null;
      selectedTextEntryId = id;
      selectedAnnotationId = null;
      lastSelectionType = 'text';
      notify('text', id);
    },

    /**
     * Clear all selections.
     * Called when user clicks empty area or explicitly clears selection.
     */
    clearSelection() {
      selectedAnnotationId = null;
      selectedTextEntryId = null;
      lastSelectionType = 'clear';
      notify('clear', null);
    },

    /**
     * Register a listener for selection changes.
     *
     * @param {SelectionListener} callback - Function called on selection change
     * @returns {function(): void} Unsubscribe function
     */
    onSelectionChange(callback) {
      if (typeof callback !== 'function') {
        throw new Error('Callback must be a function');
      }
      listeners.push(callback);

      // Return unsubscribe function
      return () => {
        const idx = listeners.indexOf(callback);
        if (idx !== -1) {
          listeners.splice(idx, 1);
        }
      };
    },

    /**
     * Get the currently selected annotation ID.
     * @returns {string|null}
     */
    getSelectedAnnotation() {
      return selectedAnnotationId;
    },

    /**
     * Get the currently selected text entry ID.
     * @returns {string|null}
     */
    getSelectedTextEntry() {
      return selectedTextEntryId;
    },

    /**
     * Get the type of the last selection.
     * @returns {SelectionType}
     */
    getLastSelectionType() {
      return lastSelectionType;
    },

    /**
     * Get current selection state snapshot.
     * @returns {SelectionState}
     */
    getState,

    /**
     * Check if an annotation is currently selected.
     * @param {string} annotationId - ID to check
     * @returns {boolean}
     */
    isAnnotationSelected(annotationId) {
      const id = String(annotationId).replace(/^#/, '');
      return selectedAnnotationId === id;
    },

    /**
     * Check if a text entry is currently selected.
     * @param {string} textEntryId - ID to check
     * @returns {boolean}
     */
    isTextEntrySelected(textEntryId) {
      return selectedTextEntryId === String(textEntryId);
    },

    /**
     * Get the Annotorious instance if available.
     * @returns {Object|null}
     */
    getAnnotorious() {
      return anno;
    }
  };
}

/**
 * Create selection handlers that wire Annotorious events to the selection manager.
 *
 * @param {Object} anno - Annotorious instance
 * @param {Object} selectionManager - Selection manager instance
 * @param {Object} indexManager - Parent index manager for finding linked entries
 * @param {Object} options - Configuration options
 * @param {function(string[]): void} [options.onHighlightTableRows] - Callback to highlight table rows
 * @param {function(string[]): void} [options.onHighlightAnnotations] - Callback to highlight annotations
 * @returns {function(): void} Cleanup function to remove event handlers
 */
export function wireAnnotoriousEvents(anno, selectionManager, indexManager, options = {}) {
  const {
    onHighlightTableRows = () => {},
    onHighlightAnnotations = () => {}
  } = options;

  // Handler for annotation selection in Annotorious
  function handleSelectAnnotation(annotation) {
    if (!annotation) {
      selectionManager.clearSelection();
      onHighlightTableRows([]);
      return;
    }

    const boxId = String(annotation.id).replace(/^#/, '');
    selectionManager.selectAnnotation(boxId);

    // Find and highlight linked text entries
    const linkedTexts = indexManager.getLinkedTextEntries(boxId);
    const textIds = linkedTexts.map(t => String(t.id));
    onHighlightTableRows(textIds);
  }

  // Handler for annotation deselection
  function handleCancelSelected() {
    selectionManager.clearSelection();
    onHighlightTableRows([]);
  }

  // Register Annotorious event handlers
  anno.on('selectAnnotation', handleSelectAnnotation);
  anno.on('cancelSelected', handleCancelSelected);

  // Return cleanup function
  return () => {
    anno.off('selectAnnotation', handleSelectAnnotation);
    anno.off('cancelSelected', handleCancelSelected);
  };
}

/**
 * Create a table row click handler.
 *
 * @param {Object} selectionManager - Selection manager instance
 * @param {Object} indexManager - Parent index manager
 * @param {Object} anno - Annotorious instance
 * @returns {function(string): void} Row click handler
 */
export function createTableRowClickHandler(selectionManager, indexManager, anno) {
  return function handleRowClick(textEntryId) {
    selectionManager.selectTextEntry(textEntryId);

    // Find linked bounding boxes
    const linkedBoxes = indexManager.getLinkedBoundingBoxes(textEntryId);

    // Clear previous selection
    if (anno.cancelSelected) {
      anno.cancelSelected();
    }

    // Highlight linked boxes
    // Note: Annotorious may not support multi-select, so we select the first one
    if (linkedBoxes.length > 0) {
      const firstBox = linkedBoxes[0];
      const annotationId = `#${firstBox.id}`;
      anno.selectAnnotation(annotationId);
    }
  };
}

/**
 * Highlight table rows by adding a CSS class.
 *
 * @param {string[]} entryIds - IDs of entries to highlight
 * @param {string} [tableSelector='#textDataTable'] - CSS selector for the table
 * @param {string} [highlightClass='highlighted'] - CSS class for highlighting
 */
export function highlightTableRows(entryIds, tableSelector = '#textDataTable', highlightClass = 'highlighted') {
  const idSet = new Set(entryIds.map(String));

  const rows = document.querySelectorAll(`${tableSelector} tbody tr`);
  for (const row of rows) {
    const rowId = row.dataset.entryId;
    row.classList.toggle(highlightClass, idSet.has(rowId));
  }
}

/**
 * Clear all table row highlights.
 *
 * @param {string} [tableSelector='#textDataTable'] - CSS selector for the table
 * @param {string} [highlightClass='highlighted'] - CSS class for highlighting
 */
export function clearTableHighlights(tableSelector = '#textDataTable', highlightClass = 'highlighted') {
  const rows = document.querySelectorAll(`${tableSelector} tbody tr.${highlightClass}`);
  for (const row of rows) {
    row.classList.remove(highlightClass);
  }
}

export default {
  createSelectionManager,
  wireAnnotoriousEvents,
  createTableRowClickHandler,
  highlightTableRows,
  clearTableHighlights
};
