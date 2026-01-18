/**
 * Annotorious W3C JSON to YAML Conversion
 *
 * Converts Annotorious W3C annotation format back to Collectra YAML format.
 *
 * Annotorious W3C format uses top-left percentage coordinates:
 *   - xywh=percent:x,y,w,h where x,y is top-left corner (0-100 range)
 *
 * Collectra format uses center-based relative coordinates (0-1 range):
 *   - x_center, y_center: center point as fraction of image dimensions
 *   - width_relative, height_relative: box dimensions as fraction of image dimensions
 */

import { normalizeToArray } from './index.js';

/**
 * Parse the xywh fragment selector value from W3C annotation.
 *
 * @param {string} selectorValue - Fragment selector value (e.g., "xywh=percent:10,20,30,40")
 * @returns {Object} Parsed coordinates { x, y, w, h } in percentage (0-100)
 * @throws {Error} If selector format is invalid
 */
export function parseFragmentSelector(selectorValue) {
  if (!selectorValue || typeof selectorValue !== 'string') {
    throw new Error('Selector value must be a non-empty string');
  }

  // Match xywh=percent:x,y,w,h format
  const match = selectorValue.match(/^xywh=percent:([\d.]+),([\d.]+),([\d.]+),([\d.]+)$/);

  if (!match) {
    throw new Error(`Invalid fragment selector format: ${selectorValue}. Expected: xywh=percent:x,y,w,h`);
  }

  const [, xStr, yStr, wStr, hStr] = match;
  const x = parseFloat(xStr);
  const y = parseFloat(yStr);
  const w = parseFloat(wStr);
  const h = parseFloat(hStr);

  // Validate parsed values
  if ([x, y, w, h].some(v => Number.isNaN(v))) {
    throw new Error(`Failed to parse coordinates from: ${selectorValue}`);
  }

  return { x, y, w, h };
}

/**
 * Extract the selector value from an annotation target.
 *
 * Handles both simple selector objects and arrays of selectors.
 *
 * @param {Object} annotation - W3C annotation object
 * @returns {string} The fragment selector value
 * @throws {Error} If no valid FragmentSelector is found
 */
export function extractSelectorValue(annotation) {
  if (!annotation?.target?.selector) {
    throw new Error('Annotation missing target.selector');
  }

  const selectors = normalizeToArray(annotation.target.selector);
  const fragmentSelector = selectors.find(s => s.type === 'FragmentSelector');

  if (!fragmentSelector) {
    throw new Error('No FragmentSelector found in annotation');
  }

  return fragmentSelector.value;
}

/**
 * Convert an Annotorious W3C annotation to Collectra YAML format.
 *
 * @param {Object} annotation - W3C Web Annotation object
 * @param {string} annotation.id - Annotation ID (may include # prefix)
 * @param {Object} annotation.target - Annotation target with selector
 * @param {Array<string>|string} parents - Parent ID(s) for hierarchy. Single parent stored as string, multiple as array.
 * @returns {Object} Collectra YAML format entry
 * @throws {Error} If annotation format is invalid
 */
export function annotoriousToYaml(annotation, parents = []) {
  if (!annotation || typeof annotation !== 'object') {
    throw new Error('annotation must be a valid object');
  }

  // Extract ID, removing # prefix if present
  const rawId = annotation.id;
  if (rawId === undefined || rawId === null) {
    throw new Error('annotation.id is required');
  }
  const id = String(rawId).replace(/^#/, '');

  // Get image source from target
  const source = annotation.target?.source;
  if (!source) {
    throw new Error('annotation.target.source is required');
  }

  // Parse selector coordinates
  const selectorValue = extractSelectorValue(annotation);
  const { x, y, w, h } = parseFragmentSelector(selectorValue);

  // Convert top-left percentage (0-100) to center-based relative (0-1)
  const width_relative = w / 100;
  const height_relative = h / 100;
  const x_center = (x / 100) + (width_relative / 2);
  const y_center = (y / 100) + (height_relative / 2);

  // Normalize parents - single parent as string, multiple as array
  const normalizedParents = normalizeToArray(parents);
  const parentsValue = normalizedParents.length === 1
    ? normalizedParents[0]
    : normalizedParents;

  return {
    id,
    data: source,
    parents: parentsValue,
    x_center,
    y_center,
    width_relative,
    height_relative
  };
}

/**
 * Convert multiple Annotorious annotations to YAML entries.
 *
 * @param {Array<Object>} annotations - Array of W3C annotations
 * @param {Array<string>|string} defaultParents - Default parent(s) if not specified per-annotation
 * @returns {Array<Object>} Array of Collectra YAML entries
 */
export function annotationsToYaml(annotations, defaultParents = []) {
  if (!Array.isArray(annotations)) {
    throw new Error('annotations must be an array');
  }

  return annotations.map(annotation => annotoriousToYaml(annotation, defaultParents));
}

export default annotoriousToYaml;
