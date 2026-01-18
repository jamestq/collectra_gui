/**
 * Parent-Child Index Builder
 *
 * Builds and maintains lookup maps to trace relationships between
 * bounding boxes and text entries in the Collectra YAML structure.
 *
 * The index enables:
 * - Finding all children of a given parent
 * - Finding all parents of a given child
 * - Linking bounding boxes to their associated text entries
 */

import { normalizeToArray } from '../converter/index.js';

/**
 * Build parent-child relationship indexes from YAML data.
 *
 * @param {Object} yamlData - Parsed Collectra YAML data
 * @returns {Object} Index with parentToChildren and childToParents maps
 */
export function buildParentIndex(yamlData) {
  /** @type {Object<string, string[]>} parentId -> [childIds] */
  const parentToChildren = {};

  /** @type {Object<string, string[]>} childId -> [parentIds] */
  const childToParents = {};

  // Collect all entries that have parent relationships
  const allEntries = [
    ...normalizeToArray(yamlData?.cropped_image_inside_root_image),
    ...normalizeToArray(yamlData?.sub_cropped_image),
    ...normalizeToArray(yamlData?.text_draft),
    ...normalizeToArray(yamlData?.text)
  ];

  for (const entry of allEntries) {
    if (!entry?.id) continue;

    const entryId = String(entry.id);
    const parents = normalizeToArray(entry.parents);

    // Store child -> parents mapping
    childToParents[entryId] = parents.map(String);

    // Store parent -> children mappings
    for (const parentId of parents) {
      const pid = String(parentId);
      if (!parentToChildren[pid]) {
        parentToChildren[pid] = [];
      }
      if (!parentToChildren[pid].includes(entryId)) {
        parentToChildren[pid].push(entryId);
      }
    }
  }

  return { parentToChildren, childToParents };
}

/**
 * Get all children of a parent entry.
 *
 * @param {string} parentId - ID of the parent entry
 * @param {Object} index - Index from buildParentIndex
 * @returns {string[]} Array of child IDs
 */
export function getChildren(parentId, index) {
  return index.parentToChildren[String(parentId)] || [];
}

/**
 * Get all parents of a child entry.
 *
 * @param {string} childId - ID of the child entry
 * @param {Object} index - Index from buildParentIndex
 * @returns {string[]} Array of parent IDs
 */
export function getParents(childId, index) {
  return index.childToParents[String(childId)] || [];
}

/**
 * Find all text entries linked to a bounding box.
 *
 * Text entries are linked if their parents include the bounding box ID.
 *
 * @param {string} boundingBoxId - ID of the bounding box
 * @param {Object} index - Index from buildParentIndex
 * @param {Object} yamlData - Full YAML data for accessing entries
 * @returns {Object[]} Array of text entry objects
 */
export function getLinkedTextEntries(boundingBoxId, index, yamlData) {
  const boxId = String(boundingBoxId);

  const textEntries = [
    ...normalizeToArray(yamlData?.text_draft),
    ...normalizeToArray(yamlData?.text)
  ];

  return textEntries.filter(entry => {
    if (!entry?.id) return false;
    const parents = normalizeToArray(entry.parents).map(String);
    return parents.includes(boxId);
  });
}

/**
 * Find all bounding boxes linked to a text entry.
 *
 * Returns bounding box entries that are parents of the text entry.
 *
 * @param {string} textEntryId - ID of the text entry
 * @param {Object} index - Index from buildParentIndex
 * @param {Object} yamlData - Full YAML data for accessing entries
 * @returns {Object[]} Array of bounding box entry objects
 */
export function getLinkedBoundingBoxes(textEntryId, index, yamlData) {
  const entryId = String(textEntryId);
  const parentIds = index.childToParents[entryId] || [];

  const allBoxes = [
    ...normalizeToArray(yamlData?.cropped_image_inside_root_image),
    ...normalizeToArray(yamlData?.sub_cropped_image)
  ];

  return allBoxes.filter(box => {
    if (!box?.id) return false;
    return parentIds.includes(String(box.id));
  });
}

/**
 * Find all descendants of an entry (recursive).
 *
 * Traverses the parent-child hierarchy to find all descendants.
 *
 * @param {string} entryId - ID of the root entry
 * @param {Object} index - Index from buildParentIndex
 * @param {Set<string>} [visited] - Set of already visited IDs (for cycle detection)
 * @returns {string[]} Array of all descendant IDs
 */
export function getDescendants(entryId, index, visited = new Set()) {
  const id = String(entryId);

  if (visited.has(id)) {
    return []; // Cycle detected, stop recursion
  }

  visited.add(id);
  const children = getChildren(id, index);
  const descendants = [...children];

  for (const childId of children) {
    descendants.push(...getDescendants(childId, index, visited));
  }

  return descendants;
}

/**
 * Find all ancestors of an entry (recursive).
 *
 * Traverses up the parent-child hierarchy to find all ancestors.
 *
 * @param {string} entryId - ID of the entry
 * @param {Object} index - Index from buildParentIndex
 * @param {Set<string>} [visited] - Set of already visited IDs (for cycle detection)
 * @returns {string[]} Array of all ancestor IDs
 */
export function getAncestors(entryId, index, visited = new Set()) {
  const id = String(entryId);

  if (visited.has(id)) {
    return []; // Cycle detected, stop recursion
  }

  visited.add(id);
  const parents = getParents(id, index);
  const ancestors = [...parents];

  for (const parentId of parents) {
    ancestors.push(...getAncestors(parentId, index, visited));
  }

  return ancestors;
}

/**
 * Check if an entry is an orphan (no valid parents exist).
 *
 * @param {string} entryId - ID of the entry
 * @param {Object} index - Index from buildParentIndex
 * @param {Object} yamlData - Full YAML data
 * @returns {boolean} True if the entry has no valid parent references
 */
export function isOrphan(entryId, index, yamlData) {
  const parentIds = getParents(entryId, index);

  if (parentIds.length === 0) {
    return true;
  }

  // Check if any parent actually exists in the data
  const allEntries = [
    yamlData?.root_image_label,
    ...normalizeToArray(yamlData?.cropped_image_inside_root_image),
    ...normalizeToArray(yamlData?.sub_cropped_image)
  ].filter(Boolean);

  const existingIds = new Set(allEntries.map(e => String(e.id)));

  return !parentIds.some(pid => existingIds.has(pid));
}

/**
 * Create an index manager that maintains the index across updates.
 *
 * @param {Object} initialYamlData - Initial YAML data
 * @returns {Object} Index manager with rebuild and query methods
 */
export function createIndexManager(initialYamlData) {
  let currentIndex = buildParentIndex(initialYamlData);
  let yamlData = initialYamlData;

  return {
    /**
     * Rebuild the index with new data.
     * @param {Object} newYamlData - Updated YAML data
     */
    rebuild(newYamlData) {
      yamlData = newYamlData;
      currentIndex = buildParentIndex(newYamlData);
    },

    /**
     * Get the current index.
     * @returns {Object} Current parent index
     */
    getIndex() {
      return currentIndex;
    },

    /**
     * Get children of a parent.
     * @param {string} parentId - Parent ID
     * @returns {string[]} Child IDs
     */
    getChildren(parentId) {
      return getChildren(parentId, currentIndex);
    },

    /**
     * Get parents of a child.
     * @param {string} childId - Child ID
     * @returns {string[]} Parent IDs
     */
    getParents(childId) {
      return getParents(childId, currentIndex);
    },

    /**
     * Get text entries linked to a bounding box.
     * @param {string} boxId - Bounding box ID
     * @returns {Object[]} Linked text entries
     */
    getLinkedTextEntries(boxId) {
      return getLinkedTextEntries(boxId, currentIndex, yamlData);
    },

    /**
     * Get bounding boxes linked to a text entry.
     * @param {string} textId - Text entry ID
     * @returns {Object[]} Linked bounding boxes
     */
    getLinkedBoundingBoxes(textId) {
      return getLinkedBoundingBoxes(textId, currentIndex, yamlData);
    }
  };
}

export default {
  buildParentIndex,
  getChildren,
  getParents,
  getLinkedTextEntries,
  getLinkedBoundingBoxes,
  getDescendants,
  getAncestors,
  isOrphan,
  createIndexManager
};
