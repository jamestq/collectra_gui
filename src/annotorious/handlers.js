/**
 * Annotorious Event Handlers
 *
 * Manages event handlers for Annotorious annotation lifecycle events.
 * Bridges Annotorious W3C format with Collectra YAML format through conversion layer.
 */

import { annotoriousToYaml } from '../converter/annotoriousToYaml.js';

/**
 * @typedef {'create' | 'update' | 'delete'} AnnotationEventType
 */

/**
 * @typedef {Object} AnnotationChange
 * @property {AnnotationEventType} type - Type of change
 * @property {Object} data - Changed annotation data (YAML format for create/update, ID for delete)
 * @property {Object} [previous] - Previous annotation data (for update events)
 */

/**
 * @typedef {function(AnnotationChange): void} AnnotationChangeCallback
 */

/**
 * Setup event handlers for Annotorious annotation lifecycle.
 *
 * @param {Object} anno - Annotorious instance
 * @param {AnnotationChangeCallback} onUpdate - Callback for annotation changes
 * @param {Object} [options={}] - Configuration options
 * @param {function(): string[]} [options.getParents] - Function to get current parent IDs for new annotations
 * @param {Object} [options.yamlData] - Current YAML data for context
 * @returns {function(): void} Cleanup function to remove event handlers
 * @throws {Error} If anno is invalid or onUpdate is not a function
 */
export function setupHandlers(anno, onUpdate, options = {}) {
  if (!anno || typeof anno.on !== 'function') {
    throw new Error('Invalid Annotorious instance');
  }

  if (typeof onUpdate !== 'function') {
    throw new Error('onUpdate must be a function');
  }

  const { getParents = () => [], yamlData = null } = options;

  /**
   * Handler for annotation creation.
   * @param {Object} annotation - W3C annotation object
   */
  function handleCreate(annotation) {
    try {
      const parents = getParents();
      const yamlEntry = annotoriousToYaml(annotation, parents);

      onUpdate({
        type: 'create',
        data: yamlEntry
      });
    } catch (err) {
      console.error('Error handling annotation creation:', err);
    }
  }

  /**
   * Handler for annotation update.
   * @param {Object} annotation - Updated W3C annotation object
   * @param {Object} previous - Previous W3C annotation object
   */
  function handleUpdate(annotation, previous) {
    try {
      const parents = getParents();
      const yamlEntry = annotoriousToYaml(annotation, parents);
      const previousYaml = previous ? annotoriousToYaml(previous, parents) : null;

      onUpdate({
        type: 'update',
        data: yamlEntry,
        previous: previousYaml
      });
    } catch (err) {
      console.error('Error handling annotation update:', err);
    }
  }

  /**
   * Handler for annotation deletion.
   * @param {Object} annotation - Deleted W3C annotation object
   */
  function handleDelete(annotation) {
    try {
      const annotationId = String(annotation.id).replace(/^#/, '');

      onUpdate({
        type: 'delete',
        data: annotationId
      });
    } catch (err) {
      console.error('Error handling annotation deletion:', err);
    }
  }

  // Register event handlers
  anno.on('createAnnotation', handleCreate);
  anno.on('updateAnnotation', handleUpdate);
  anno.on('deleteAnnotation', handleDelete);

  // Return cleanup function
  return function cleanup() {
    anno.off('createAnnotation', handleCreate);
    anno.off('updateAnnotation', handleUpdate);
    anno.off('deleteAnnotation', handleDelete);
  };
}

/**
 * Create a parent context manager for tracking which parent to assign to new annotations.
 *
 * @param {string} [defaultParent] - Default parent ID
 * @returns {Object} Parent context manager
 */
export function createParentContext(defaultParent = null) {
  let currentParents = defaultParent ? [defaultParent] : [];

  return {
    /**
     * Set the current parent context.
     * @param {string|string[]} parents - Parent ID(s)
     */
    setParents(parents) {
      if (Array.isArray(parents)) {
        currentParents = parents;
      } else if (parents) {
        currentParents = [parents];
      } else {
        currentParents = [];
      }
    },

    /**
     * Get current parent context.
     * @returns {string[]} Current parent IDs
     */
    getParents() {
      return [...currentParents];
    },

    /**
     * Clear parent context.
     */
    clear() {
      currentParents = [];
    },

    /**
     * Check if a parent context is set.
     * @returns {boolean}
     */
    hasParents() {
      return currentParents.length > 0;
    }
  };
}

export default {
  setupHandlers,
  createParentContext
};
