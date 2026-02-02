import { getActiveCandidates, searchCandidates } from '../data/candidates.js';

export function renderCandidateList(container, { onSelect, selectedIds = [] }) {
  const candidates = getActiveCandidates();
  
  if (candidates.length === 0) {
    container.innerHTML = `<div class="empty-state">No active candidates</div>`;
    return;
  }
  
  container.innerHTML = `
    <ul class="list">
      ${candidates.map(c => {
        const metaParts = [normalizeMeta(c.title), normalizeMeta(c.location)].filter(Boolean);
        const meta = metaParts.length > 0 ? metaParts.join(' • ') : '';
        return `
        <li class="list-item ${selectedIds.includes(c.id) ? 'selected' : ''}" data-id="${c.id}">
          <div class="candidate-name">${c.name}</div>
          ${meta ? `<div class="candidate-title">${meta}</div>` : ''}
        </li>
      `;
      }).join('')}
    </ul>
  `;
  
  container.querySelectorAll('.list-item').forEach(item => {
    item.addEventListener('click', () => onSelect?.(item.dataset.id));
  });
}

export function filterCandidateList(container, query, options = {}) {
  const results = searchCandidates(query, options.filters);
  const { onSelect, selectedIds = [] } = options;
  
  if (results.length === 0) {
    container.innerHTML = `<div class="empty-state">No candidates match "${query}"</div>`;
    return;
  }
  
  container.innerHTML = `
    <ul class="list">
      ${results.map(c => {
        const metaParts = [normalizeMeta(c.title), normalizeMeta(c.location)].filter(Boolean);
        const meta = metaParts.length > 0 ? metaParts.join(' • ') : '';
        return `
        <li class="list-item ${selectedIds.includes(c.id) ? 'selected' : ''}" data-id="${c.id}">
          <div class="candidate-name">${c.name}</div>
          ${meta ? `<div class="candidate-title">${meta}</div>` : ''}
        </li>
      `;
      }).join('')}
    </ul>
  `;
  
  container.querySelectorAll('.list-item').forEach(item => {
    item.addEventListener('click', () => onSelect?.(item.dataset.id));
  });
}

function normalizeMeta(value) {
  if (!value) return '';
  if (typeof value !== 'string') return value;
  const trimmed = value.trim();
  const lowered = trimmed.toLowerCase();
  if (!trimmed || lowered === 'null' || lowered === 'undefined') return '';
  return trimmed;
}
