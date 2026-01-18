/**
 * Annotorious Module
 *
 * Exports setup and event handler utilities for Annotorious integration.
 */

export {
  initAnnotorious,
  loadAnnotations,
  clearAnnotations,
  destroyAnnotorious
} from './setup.js';

export {
  setupHandlers,
  createParentContext
} from './handlers.js';
