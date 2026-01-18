/**
 * Text Data Table Renderer
 *
 * Renders text and text_draft entries in an HTML table with inline editing capabilities.
 * Displays linked bounding boxes and provides delete functionality.
 */

import { normalizeToArray } from '../io/loadCollectra.js';

/**
 * Render the text data table with all text and text_draft entries.
 *
 * @param {Object} yamlData - Collectra YAML data
 * @param {Object} indexManager - Parent index manager for finding linked boxes
 * @param {Object} handlers - Event handlers
 * @param {function(string): void} handlers.onRowClick - Called when row is clicked
 * @param {function(string, string): void} handlers.onTextEdit - Called when text cell is edited
 * @param {function(string): void} handlers.onDelete - Called when delete button is clicked
 * @param {string} [tableSelector='#textDataTable'] - CSS selector for table element
 */
export function renderTextTable(yamlData, indexManager, handlers, tableSelector = '#textDataTable') {
  const { onRowClick, onTextEdit, onDelete } = handlers;

  const table = document.querySelector(tableSelector);
  if (!table) {
    console.error(`Table not found: ${tableSelector}`);
    return;
  }

  const tbody = table.querySelector('tbody');
  if (!tbody) {
    console.error(`Table body not found in ${tableSelector}`);
    return;
  }

  // Clear existing rows
  tbody.innerHTML = '';

  // Collect all text entries with type annotation
  const textEntries = [
    ...normalizeToArray(yamlData.text_draft).map(e => ({ ...e, type: 'draft' })),
    ...normalizeToArray(yamlData.text).map(e => ({ ...e, type: 'final' }))
  ];

  // Sort by ID for consistent ordering
  textEntries.sort((a, b) => String(a.id).localeCompare(String(b.id)));

  // Render each entry as a table row
  for (const entry of textEntries) {
    const row = createTableRow(entry, indexManager, yamlData, handlers);
    tbody.appendChild(row);
  }

  // Show empty state if no entries
  if (textEntries.length === 0) {
    const emptyRow = document.createElement('tr');
    emptyRow.className = 'empty-row';
    emptyRow.innerHTML = '<td colspan="5" style="text-align: center; color: #999;">No text entries found</td>';
    tbody.appendChild(emptyRow);
  }
}

/**
 * Create a single table row for a text entry.
 *
 * @param {Object} entry - Text entry data
 * @param {Object} indexManager - Parent index manager
 * @param {Object} yamlData - Full YAML data
 * @param {Object} handlers - Event handlers
 * @returns {HTMLTableRowElement} Table row element
 */
function createTableRow(entry, indexManager, yamlData, handlers) {
  const { onRowClick, onTextEdit, onDelete } = handlers;

  const row = document.createElement('tr');
  row.dataset.entryId = entry.id;

  // Find linked bounding boxes
  const linkedBoxes = indexManager.getLinkedBoundingBoxes(String(entry.id));
  const linkedBoxIds = linkedBoxes.map(b => String(b.id)).join(', ') || 'None';

  // Create cells
  const idCell = document.createElement('td');
  idCell.textContent = entry.id;
  idCell.className = 'id-cell';

  const typeCell = document.createElement('td');
  const typeBadge = document.createElement('span');
  typeBadge.className = `badge badge-${entry.type}`;
  typeBadge.textContent = entry.type;
  typeCell.appendChild(typeBadge);

  const textCell = document.createElement('td');
  textCell.contentEditable = 'true';
  textCell.className = 'editable-cell';
  textCell.textContent = entry.data || '';

  // Handle text editing
  textCell.addEventListener('blur', (e) => {
    const newText = e.target.textContent;
    if (newText !== entry.data) {
      onTextEdit(String(entry.id), newText);
    }
  });

  // Prevent newlines in contenteditable
  textCell.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      textCell.blur(); // Commit the edit
    }
  });

  const linkedCell = document.createElement('td');
  linkedCell.textContent = linkedBoxIds;
  linkedCell.className = 'linked-boxes-cell';

  const actionsCell = document.createElement('td');
  const deleteBtn = document.createElement('button');
  deleteBtn.className = 'btn-delete';
  deleteBtn.textContent = 'Delete';
  deleteBtn.dataset.id = entry.id;
  deleteBtn.addEventListener('click', (e) => {
    e.stopPropagation(); // Prevent row click
    if (confirm(`Delete text entry "${entry.id}"?`)) {
      onDelete(String(entry.id));
    }
  });
  actionsCell.appendChild(deleteBtn);

  // Assemble row
  row.appendChild(idCell);
  row.appendChild(typeCell);
  row.appendChild(textCell);
  row.appendChild(linkedCell);
  row.appendChild(actionsCell);

  // Handle row click (not on editable cell or delete button)
  row.addEventListener('click', (e) => {
    // Don't trigger if clicking in editable cell or delete button
    if (e.target.classList.contains('editable-cell') ||
        e.target.classList.contains('btn-delete')) {
      return;
    }
    onRowClick(String(entry.id));
  });

  return row;
}

/**
 * Highlight specific table rows.
 *
 * @param {string[]} entryIds - IDs of entries to highlight
 * @param {string} [tableSelector='#textDataTable'] - CSS selector for table
 * @param {string} [highlightClass='highlighted'] - CSS class for highlighting
 */
export function highlightRows(entryIds, tableSelector = '#textDataTable', highlightClass = 'highlighted') {
  const idSet = new Set(entryIds.map(String));

  const table = document.querySelector(tableSelector);
  if (!table) return;

  const rows = table.querySelectorAll('tbody tr');
  for (const row of rows) {
    const rowId = row.dataset.entryId;
    row.classList.toggle(highlightClass, idSet.has(rowId));
  }
}

/**
 * Clear all table row highlights.
 *
 * @param {string} [tableSelector='#textDataTable'] - CSS selector for table
 * @param {string} [highlightClass='highlighted'] - CSS class for highlighting
 */
export function clearHighlights(tableSelector = '#textDataTable', highlightClass = 'highlighted') {
  const table = document.querySelector(tableSelector);
  if (!table) return;

  const rows = table.querySelectorAll(`tbody tr.${highlightClass}`);
  for (const row of rows) {
    row.classList.remove(highlightClass);
  }
}

/**
 * Scroll a table row into view.
 *
 * @param {string} entryId - ID of entry to scroll to
 * @param {string} [tableSelector='#textDataTable'] - CSS selector for table
 */
export function scrollToRow(entryId, tableSelector = '#textDataTable') {
  const table = document.querySelector(tableSelector);
  if (!table) return;

  const row = table.querySelector(`tbody tr[data-entry-id="${entryId}"]`);
  if (row) {
    row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

export default {
  renderTextTable,
  highlightRows,
  clearHighlights,
  scrollToRow
};
