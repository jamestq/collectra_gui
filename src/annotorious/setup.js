/**
 * Annotorious Setup Module
 *
 * Initializes and configures the Annotorious annotation library for bounding box editing.
 * Provides setup functions for creating Annotorious instances with optimal configuration.
 */

import { Annotorious } from '@annotorious/annotorious';
import '@annotorious/annotorious/annotorious.css';

/**
 * Initialize Annotorious on an image element.
 *
 * @param {HTMLImageElement} imageElement - The image element to annotate
 * @param {Object} [options={}] - Configuration options
 * @param {boolean} [options.drawOnSingleClick=true] - Enable drawing on single click
 * @param {boolean} [options.allowEmpty=false] - Allow empty annotations
 * @param {boolean} [options.readOnly=false] - Make annotations read-only
 * @returns {Object} Annotorious instance
 * @throws {Error} If imageElement is not a valid HTMLImageElement
 */
export function initAnnotorious(imageElement, options = {}) {
  if (!imageElement || !(imageElement instanceof HTMLElement)) {
    throw new Error('imageElement must be a valid HTML element');
  }

  const {
    drawOnSingleClick = true,
    allowEmpty = false,
    readOnly = false
  } = options;

  const anno = new Annotorious({
    image: imageElement,
    drawOnSingleClick,
    allowEmpty,
    readOnly
  });

  return anno;
}

/**
 * Load annotations into Annotorious instance.
 *
 * @param {Object} anno - Annotorious instance
 * @param {Array<Object>} annotations - Array of W3C annotations
 * @throws {Error} If anno is not valid or annotations is not an array
 */
export function loadAnnotations(anno, annotations) {
  if (!anno || typeof anno.setAnnotations !== 'function') {
    throw new Error('Invalid Annotorious instance');
  }

  if (!Array.isArray(annotations)) {
    throw new Error('annotations must be an array');
  }

  // Clear existing annotations
  anno.clearAnnotations();

  // Add annotations one by one
  for (const annotation of annotations) {
    try {
      anno.addAnnotation(annotation);
    } catch (err) {
      console.error('Failed to add annotation:', annotation, err);
    }
  }
}

/**
 * Clear all annotations from Annotorious instance.
 *
 * @param {Object} anno - Annotorious instance
 */
export function clearAnnotations(anno) {
  if (anno && typeof anno.clearAnnotations === 'function') {
    anno.clearAnnotations();
  }
}

/**
 * Destroy Annotorious instance and cleanup.
 *
 * @param {Object} anno - Annotorious instance
 */
export function destroyAnnotorious(anno) {
  if (anno && typeof anno.destroy === 'function') {
    anno.destroy();
  }
}

export default {
  initAnnotorious,
  loadAnnotations,
  clearAnnotations,
  destroyAnnotorious
};
