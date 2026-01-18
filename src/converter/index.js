/**
 * Converter Module Index
 *
 * Central export point for YAML <-> Annotorious W3C JSON conversion utilities.
 */

// Utility functions (exported first as they're used by other modules)

/**
 * Normalize a value to an array.
 * - undefined/null -> []
 * - array -> array (as-is)
 * - single value -> [value]
 *
 * @param {*} value - Value to normalize
 * @returns {Array} Normalized array
 */
export function normalizeToArray(value) {
  if (value === undefined || value === null) {
    return [];
  }
  return Array.isArray(value) ? value : [value];
}

/**
 * Validate that coordinates are within the valid 0-1 range.
 *
 * @param {Object} coords - Coordinate object with x_center, y_center, width_relative, height_relative
 * @returns {boolean} True if all coordinates are valid
 */
export function validateRelativeCoordinates(coords) {
  const { x_center, y_center, width_relative, height_relative } = coords;

  const isInRange = (val) => typeof val === 'number' && val >= 0 && val <= 1;

  return (
    isInRange(x_center) &&
    isInRange(y_center) &&
    isInRange(width_relative) &&
    isInRange(height_relative)
  );
}

/**
 * Clamp a value to a range.
 *
 * @param {number} value - Value to clamp
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @returns {number} Clamped value
 */
export function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

// Conversion functions
export { yamlToAnnotorious, yamlEntriesToAnnotorious } from './yamlToAnnotorious.js';
export {
  annotoriousToYaml,
  annotationsToYaml,
  parseFragmentSelector,
  extractSelectorValue
} from './annotoriousToYaml.js';

// Default export with all utilities grouped
export default {
  normalizeToArray,
  validateRelativeCoordinates,
  clamp
};
