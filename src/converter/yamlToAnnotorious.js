/**
 * YAML to Annotorious W3C JSON Conversion
 *
 * Converts Collectra YAML bounding box entries to Annotorious W3C annotation format.
 *
 * Collectra format uses center-based relative coordinates (0-1 range):
 *   - x_center, y_center: center point as fraction of image dimensions
 *   - width_relative, height_relative: box dimensions as fraction of image dimensions
 *
 * Annotorious W3C format uses top-left percentage coordinates:
 *   - xywh=percent:x,y,w,h where x,y is top-left corner (0-100 range)
 */

/**
 * Convert a single YAML bounding box entry to Annotorious W3C annotation format.
 *
 * @param {Object} yamlEntry - Collectra YAML entry with bounding box data
 * @param {string} yamlEntry.id - Unique identifier for the annotation
 * @param {number} yamlEntry.x_center - X center position (0-1 relative)
 * @param {number} yamlEntry.y_center - Y center position (0-1 relative)
 * @param {number} yamlEntry.width_relative - Width as fraction of image (0-1)
 * @param {number} yamlEntry.height_relative - Height as fraction of image (0-1)
 * @param {string} imageSource - Image URL or path for the annotation target
 * @returns {Object} W3C Web Annotation format object
 * @throws {Error} If required fields are missing or coordinates are invalid
 */
export function yamlToAnnotorious(yamlEntry, imageSource) {
  // Validate required fields
  if (!yamlEntry || typeof yamlEntry !== 'object') {
    throw new Error('yamlEntry must be a valid object');
  }

  const { id, x_center, y_center, width_relative, height_relative } = yamlEntry;

  if (id === undefined || id === null) {
    throw new Error('yamlEntry.id is required');
  }

  if (!imageSource) {
    throw new Error('imageSource is required');
  }

  // Validate coordinate fields exist and are numbers
  const coords = { x_center, y_center, width_relative, height_relative };
  for (const [key, value] of Object.entries(coords)) {
    if (typeof value !== 'number' || Number.isNaN(value)) {
      throw new Error(`${key} must be a valid number, got: ${value}`);
    }
  }

  // Validate coordinate ranges (0-1 for relative coordinates)
  if (x_center < 0 || x_center > 1) {
    throw new Error(`x_center must be between 0 and 1, got: ${x_center}`);
  }
  if (y_center < 0 || y_center > 1) {
    throw new Error(`y_center must be between 0 and 1, got: ${y_center}`);
  }
  if (width_relative < 0 || width_relative > 1) {
    throw new Error(`width_relative must be between 0 and 1, got: ${width_relative}`);
  }
  if (height_relative < 0 || height_relative > 1) {
    throw new Error(`height_relative must be between 0 and 1, got: ${height_relative}`);
  }

  // Convert center-based relative coords (0-1) to top-left percentage (0-100)
  // x_percent = (x_center - width/2) * 100
  const x = (x_center - width_relative / 2) * 100;
  const y = (y_center - height_relative / 2) * 100;
  const w = width_relative * 100;
  const h = height_relative * 100;

  // Clamp values to valid percentage range [0, 100]
  const clamp = (val, min, max) => Math.max(min, Math.min(max, val));
  const xClamped = clamp(x, 0, 100);
  const yClamped = clamp(y, 0, 100);
  const wClamped = clamp(w, 0, 100 - xClamped);
  const hClamped = clamp(h, 0, 100 - yClamped);

  return {
    '@context': 'http://www.w3.org/ns/anno.jsonld',
    id: `#${id}`,
    type: 'Annotation',
    body: [],
    target: {
      source: imageSource,
      selector: {
        type: 'FragmentSelector',
        conformsTo: 'http://www.w3.org/TR/media-frags/',
        value: `xywh=percent:${xClamped},${yClamped},${wClamped},${hClamped}`
      }
    }
  };
}

/**
 * Convert multiple YAML entries to Annotorious annotations.
 *
 * @param {Array<Object>} yamlEntries - Array of Collectra YAML entries
 * @param {string} imageSource - Image URL or path
 * @returns {Array<Object>} Array of W3C annotations
 */
export function yamlEntriesToAnnotorious(yamlEntries, imageSource) {
  if (!Array.isArray(yamlEntries)) {
    throw new Error('yamlEntries must be an array');
  }

  return yamlEntries.map(entry => yamlToAnnotorious(entry, imageSource));
}

export default yamlToAnnotorious;
