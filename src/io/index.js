/**
 * I/O Module
 *
 * Exports functions for loading and saving Collectra YAML data.
 */

export {
  loadCollectra,
  normalizeToArray
} from './loadCollectra.js';

export {
  saveCollectra,
  downloadYaml,
  copyToClipboard
} from './saveCollectra.js';
