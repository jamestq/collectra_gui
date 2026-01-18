/**
 * State Module Index
 *
 * Central export point for state management utilities.
 */

export {
  buildParentIndex,
  getChildren,
  getParents,
  getLinkedTextEntries,
  getLinkedBoundingBoxes,
  getDescendants,
  getAncestors,
  isOrphan,
  createIndexManager
} from './parentIndex.js';

export {
  createSelectionManager,
  wireAnnotoriousEvents,
  createTableRowClickHandler,
  highlightTableRows,
  clearTableHighlights
} from './selectionManager.js';
