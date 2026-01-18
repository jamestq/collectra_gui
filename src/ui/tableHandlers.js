/**
 * Text Table Event Handlers
 *
 * Provides handler functions for table interactions: row clicks, text edits, and deletions.
 * Integrates with the state manager and annotation system.
 */

/**
 * Create table event handlers.
 *
 * @param {Object} context - Application context
 * @param {Object} context.yamlData - Current YAML data
 * @param {Object} context.indexManager - Parent index manager
 * @param {Object} context.selectionManager - Selection state manager
 * @param {Object} context.anno - Annotorious instance
 * @param {function(): void} context.onDataChange - Callback when data changes
 * @returns {Object} Handler functions
 */
export function createTableHandlers(context) {
  const { yamlData, indexManager, selectionManager, anno, onDataChange } = context;

  /**
   * Handle table row click.
   * Selects the text entry and highlights linked bounding boxes.
   *
   * @param {string} textEntryId - ID of clicked text entry
   */
  function handleRowClick(textEntryId) {
    // Update selection state
    selectionManager.selectTextEntry(textEntryId);

    // Find linked bounding boxes
    const linkedBoxes = indexManager.getLinkedBoundingBoxes(textEntryId);

    // Clear previous annotation selection
    if (anno && anno.cancelSelected) {
      anno.cancelSelected();
    }

    // Select linked annotations in Annotorious
    if (linkedBoxes.length > 0 && anno) {
      // Annotorious typically only supports single selection
      // Select the first linked box
      const firstBox = linkedBoxes[0];
      const annotationId = `#${firstBox.id}`;

      if (anno.selectAnnotation) {
        try {
          anno.selectAnnotation(annotationId);
        } catch (err) {
          console.warn('Failed to select annotation:', err);
        }
      }
    }
  }

  /**
   * Handle text cell edit.
   * Updates the YAML data and triggers re-render.
   *
   * @param {string} textEntryId - ID of edited text entry
   * @param {string} newText - New text content
   */
  function handleTextEdit(textEntryId, newText) {
    // Find and update the entry in YAML data
    let updated = false;

    // Check text_draft entries
    if (yamlData.text_draft) {
      const entries = Array.isArray(yamlData.text_draft)
        ? yamlData.text_draft
        : [yamlData.text_draft];

      const entry = entries.find(e => String(e.id) === String(textEntryId));
      if (entry) {
        entry.data = newText;
        updated = true;
      }
    }

    // Check text entries if not found in drafts
    if (!updated && yamlData.text) {
      const entries = Array.isArray(yamlData.text)
        ? yamlData.text
        : [yamlData.text];

      const entry = entries.find(e => String(e.id) === String(textEntryId));
      if (entry) {
        entry.data = newText;
        updated = true;
      }
    }

    if (updated) {
      // Notify of data change
      onDataChange();
    } else {
      console.warn(`Text entry not found: ${textEntryId}`);
    }
  }

  /**
   * Handle text entry deletion.
   * Removes the entry from YAML data and triggers re-render.
   *
   * @param {string} textEntryId - ID of text entry to delete
   */
  function handleDelete(textEntryId) {
    let deleted = false;

    // Delete from text_draft
    if (yamlData.text_draft) {
      if (Array.isArray(yamlData.text_draft)) {
        const index = yamlData.text_draft.findIndex(e => String(e.id) === String(textEntryId));
        if (index !== -1) {
          yamlData.text_draft.splice(index, 1);
          // If array becomes empty, set to null
          if (yamlData.text_draft.length === 0) {
            yamlData.text_draft = null;
          }
          deleted = true;
        }
      } else if (String(yamlData.text_draft.id) === String(textEntryId)) {
        yamlData.text_draft = null;
        deleted = true;
      }
    }

    // Delete from text if not found in drafts
    if (!deleted && yamlData.text) {
      if (Array.isArray(yamlData.text)) {
        const index = yamlData.text.findIndex(e => String(e.id) === String(textEntryId));
        if (index !== -1) {
          yamlData.text.splice(index, 1);
          if (yamlData.text.length === 0) {
            yamlData.text = null;
          }
          deleted = true;
        }
      } else if (String(yamlData.text.id) === String(textEntryId)) {
        yamlData.text = null;
        deleted = true;
      }
    }

    if (deleted) {
      // Clear selection if deleted entry was selected
      if (selectionManager.getSelectedTextEntry() === textEntryId) {
        selectionManager.clearSelection();
      }

      // Notify of data change
      onDataChange();
    } else {
      console.warn(`Text entry not found for deletion: ${textEntryId}`);
    }
  }

  return {
    onRowClick: handleRowClick,
    onTextEdit: handleTextEdit,
    onDelete: handleDelete
  };
}

export default {
  createTableHandlers
};
