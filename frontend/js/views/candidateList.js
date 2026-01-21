import { getActiveCandidates, searchCandidates } from '../data/candidates.js';

export function renderCandidateList(container, { onSelect, selectedIds = [] }) {
  const candidates = getActiveCandidates();
  
  if (candidates.length === 0) {
    container.innerHTML = `<div class="empty-state">No active candidates</div>`;
    return;
  }
  
  container.innerHTML = `
    <ul class="list">
      ${candidates.map(c => `
        <li class="list-item ${selectedIds.includes(c.id) ? 'selected' : ''}" data-id="${c.id}">
          <div class="candidate-name">${c.name}</div>
          <div class="candidate-title">${c.title}</div>
          <div class="candidate-meta">${c.location}</div>
        </li>
      `).join('')}
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
      ${results.map(c => `
        <li class="list-item ${selectedIds.includes(c.id) ? 'selected' : ''}" data-id="${c.id}">
          <div class="candidate-name">${c.name}</div>
          <div class="candidate-title">${c.title}</div>
          <div class="candidate-meta">${c.location}</div>
        </li>
      `).join('')}
    </ul>
  `;
  
  container.querySelectorAll('.list-item').forEach(item => {
    item.addEventListener('click', () => onSelect?.(item.dataset.id));
  });
}
