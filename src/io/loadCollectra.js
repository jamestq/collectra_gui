/**
 * Collectra Folder Loader
 *
 * Loads and parses Collectra YAML data from the results.yaml file.
 * Handles folder structure and YAML parsing with js-yaml library.
 */

import { normalizeToArray as normalizeArrayUtil } from '../converter/index.js';

/**
 * Load Collectra data from a folder path.
 *
 * In a browser environment, this expects the YAML data to be fetched via HTTP.
 * For Node.js environments, it would read from the filesystem.
 *
 * @param {string} folderPath - Path to the .collectra folder or URL
 * @returns {Promise<Object>} Parsed YAML data
 * @throws {Error} If loading or parsing fails
 */
export async function loadCollectra(folderPath) {
  if (!folderPath) {
    throw new Error('folderPath is required');
  }

  // Construct path to results.yaml
  const yamlPath = folderPath.endsWith('/')
    ? `${folderPath}results.yaml`
    : `${folderPath}/results.yaml`;

  try {
    // Fetch the YAML file
    const response = await fetch(yamlPath);

    if (!response.ok) {
      throw new Error(`Failed to fetch ${yamlPath}: ${response.status} ${response.statusText}`);
    }

    const yamlText = await response.text();

    // Parse YAML using js-yaml (loaded via CDN in HTML)
    if (typeof jsyaml === 'undefined') {
      throw new Error('js-yaml library not loaded. Include it via script tag in HTML.');
    }

    const data = jsyaml.load(yamlText);

    // Normalize parent fields to arrays
    const normalized = normalizeParents(data);

    return normalized;
  } catch (err) {
    throw new Error(`Failed to load Collectra data from ${folderPath}: ${err.message}`);
  }
}

/**
 * Normalize parent fields to arrays.
 * In YAML, single values are stored as scalars, but we want consistent array handling.
 *
 * @param {Object} data - Raw YAML data
 * @returns {Object} Normalized data
 */
function normalizeParents(data) {
  if (!data || typeof data !== 'object') {
    return data;
  }

  const normalized = { ...data };

  // Process each key that might contain entries with parent fields
  const entryKeys = [
    'cropped_image_inside_root_image',
    'sub_cropped_image',
    'text_draft',
    'text'
  ];

  for (const key of entryKeys) {
    if (normalized[key]) {
      normalized[key] = normalizeEntries(normalized[key]);
    }
  }

  return normalized;
}

/**
 * Normalize entries to ensure parents field is always an array.
 *
 * @param {Object|Array<Object>} entries - Entry or array of entries
 * @returns {Array<Object>} Normalized entries
 */
function normalizeEntries(entries) {
  // Convert single entry to array
  const entryArray = Array.isArray(entries) ? entries : [entries];

  // Normalize each entry's parents field
  return entryArray.map(entry => {
    if (!entry || typeof entry !== 'object') {
      return entry;
    }

    const normalized = { ...entry };

    if (normalized.parents !== undefined && normalized.parents !== null) {
      // Convert single parent to array
      if (!Array.isArray(normalized.parents)) {
        normalized.parents = [normalized.parents];
      }
    } else {
      // Default to empty array if no parents
      normalized.parents = [];
    }

    return normalized;
  });
}

/**
 * Utility to convert value to array (used by other modules).
 *
 * @param {*} value - Value to normalize
 * @returns {Array} Array representation
 */
export function normalizeToArray(value) {
  return normalizeArrayUtil(value);
}

export default {
  loadCollectra,
  normalizeToArray
};
