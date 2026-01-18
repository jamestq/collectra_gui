/**
 * Collectra Folder Saver
 *
 * Serializes and saves Collectra data back to YAML format.
 * Handles denormalization of arrays to single values where appropriate.
 */

/**
 * Save Collectra data to a folder path.
 *
 * In a browser environment, this generates downloadable YAML content.
 * For Node.js, it would write to the filesystem.
 *
 * @param {string} folderPath - Path to the .collectra folder
 * @param {Object} data - Collectra data to save
 * @returns {Promise<string>} YAML string content
 * @throws {Error} If serialization fails
 */
export async function saveCollectra(folderPath, data) {
  if (!data || typeof data !== 'object') {
    throw new Error('data must be a valid object');
  }

  try {
    // Denormalize data (convert single-element arrays back to scalars)
    const denormalized = denormalizeParents(data);

    // Serialize to YAML using js-yaml
    if (typeof jsyaml === 'undefined') {
      throw new Error('js-yaml library not loaded. Include it via script tag in HTML.');
    }

    const yamlText = jsyaml.dump(denormalized, {
      indent: 2,
      lineWidth: -1, // No line wrapping
      noRefs: true,
      sortKeys: false
    });

    return yamlText;
  } catch (err) {
    throw new Error(`Failed to save Collectra data: ${err.message}`);
  }
}

/**
 * Download YAML content as a file (browser environment).
 *
 * @param {string} yamlContent - YAML string to download
 * @param {string} [filename='results.yaml'] - Filename for download
 */
export function downloadYaml(yamlContent, filename = 'results.yaml') {
  const blob = new Blob([yamlContent], { type: 'text/yaml;charset=utf-8' });
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.style.display = 'none';

  document.body.appendChild(link);
  link.click();

  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Denormalize parent fields from arrays back to scalars when appropriate.
 * YAML convention: single values should be scalars, not single-element arrays.
 *
 * @param {Object} data - Normalized data
 * @returns {Object} Denormalized data
 */
function denormalizeParents(data) {
  if (!data || typeof data !== 'object') {
    return data;
  }

  const denormalized = { ...data };

  const entryKeys = [
    'cropped_image_inside_root_image',
    'sub_cropped_image',
    'text_draft',
    'text'
  ];

  for (const key of entryKeys) {
    if (denormalized[key]) {
      denormalized[key] = denormalizeEntries(denormalized[key]);
    }
  }

  return denormalized;
}

/**
 * Denormalize entries to convert single-parent arrays back to scalars.
 *
 * @param {Array<Object>} entries - Array of entries
 * @returns {Object|Array<Object>} Denormalized entries (single entry as object, multiple as array)
 */
function denormalizeEntries(entries) {
  if (!Array.isArray(entries)) {
    return entries;
  }

  // Denormalize each entry's parents field
  const denormalized = entries.map(entry => {
    if (!entry || typeof entry !== 'object') {
      return entry;
    }

    const result = { ...entry };

    // Convert single-element parent array to scalar
    if (Array.isArray(result.parents)) {
      if (result.parents.length === 0) {
        delete result.parents; // Remove empty parents array
      } else if (result.parents.length === 1) {
        result.parents = result.parents[0]; // Convert to scalar
      }
    }

    return result;
  });

  // If only one entry, return as object instead of array
  if (denormalized.length === 1) {
    return denormalized[0];
  }

  return denormalized;
}

/**
 * Copy YAML content to clipboard (browser environment).
 *
 * @param {string} yamlContent - YAML string to copy
 * @returns {Promise<void>}
 */
export async function copyToClipboard(yamlContent) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    await navigator.clipboard.writeText(yamlContent);
  } else {
    // Fallback for older browsers
    const textarea = document.createElement('textarea');
    textarea.value = yamlContent;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
  }
}

export default {
  saveCollectra,
  downloadYaml,
  copyToClipboard
};
