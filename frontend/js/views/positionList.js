import { getOpenPositions, getPositionById, searchPositions } from '../data/positions.js';
import { getCandidatesByPosition } from '../data/candidates.js';

export function renderPositionList(container, { onSelect, selectedId }) {
  const positions = getOpenPositions();
  
  if (positions.length === 0) {
    container.innerHTML = `<div class="empty-state">No open positions</div>`;
    return;
  }
  
  container.innerHTML = `
    <ul class="list">
      ${positions.map(p => `
        <li class="list-item ${selectedId === p.id ? 'selected' : ''}" data-id="${p.id}">
          <div class="candidate-name">${p.title}</div>
          <div class="candidate-title">${p.department}</div>
          <div class="candidate-meta">${p.location}</div>
        </li>
      `).join('')}
    </ul>
  `;
  
  container.querySelectorAll('.list-item').forEach(item => {
    item.addEventListener('click', () => onSelect?.(item.dataset.id));
  });
}

export function renderPositionDetail(container, positionId) {
  const position = getPositionById(positionId);
  
  if (!position) {
    container.innerHTML = `<div class="empty-state">Select a position to view details</div>`;
    return;
  }
  
  const candidates = getCandidatesByPosition(positionId);
  
  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <div>
          <h2 class="card-title">${position.title}</h2>
          <div class="candidate-title">${position.department} • ${position.location}</div>
        </div>
        <span class="position-status status-${position.status}">${position.status.toUpperCase()}</span>
      </div>
      
      ${position.summary ? `
        <div class="profile-section">
          <h3>Summary</h3>
          <p class="text-sm">${position.summary}</p>
        </div>
      ` : ''}
      
      ${position.responsibilities.length > 0 ? `
        <div class="profile-section">
          <h3>Responsibilities</h3>
          <ul class="text-sm" style="padding-left: 1.25rem;">
            ${position.responsibilities.map(r => `<li>${r}</li>`).join('')}
          </ul>
        </div>
      ` : ''}
      
      ${position.requirements.length > 0 ? `
        <div class="profile-section">
          <h3>Requirements</h3>
          <ul class="text-sm" style="padding-left: 1.25rem;">
            ${position.requirements.map(r => `<li>${r}</li>`).join('')}
          </ul>
        </div>
      ` : ''}
      
      ${position.niceToHave.length > 0 ? `
        <div class="profile-section">
          <h3>Nice to Have</h3>
          <ul class="text-sm" style="padding-left: 1.25rem;">
            ${position.niceToHave.map(r => `<li>${r}</li>`).join('')}
          </ul>
        </div>
      ` : ''}
      
      ${position.salaryRange ? `
        <div class="profile-section">
          <h3>Compensation</h3>
          <div class="text-sm">
            ${formatCurrency(position.salaryRange.min, position.salaryRange.currency)} – 
            ${formatCurrency(position.salaryRange.max, position.salaryRange.currency)}
          </div>
        </div>
      ` : ''}
      
      <div class="profile-section">
        <h3>Candidates (${candidates.length})</h3>
        ${candidates.length > 0 
          ? `<ul class="list">
              ${candidates.map(c => `
                <li class="list-item">
                  <div class="candidate-name">${c.name}</div>
                  <div class="candidate-title">${c.title}</div>
                </li>
              `).join('')}
            </ul>`
          : '<span class="text-muted text-sm">No candidates assigned yet</span>'
        }
      </div>
    </div>
  `;
}

function formatCurrency(amount, currency = 'USD') {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency, maximumFractionDigits: 0 }).format(amount);
}

export function filterPositionList(container, query, options = {}) {
  const results = searchPositions(query, options.filters);
  const { onSelect, selectedId } = options;
  
  if (results.length === 0) {
    container.innerHTML = `<div class="empty-state">No positions match "${query}"</div>`;
    return;
  }
  
  container.innerHTML = `
    <ul class="list">
      ${results.map(p => `
        <li class="list-item ${selectedId === p.id ? 'selected' : ''}" data-id="${p.id}">
          <div class="candidate-name">${p.title}</div>
          <div class="candidate-title">${p.department}</div>
          <div class="candidate-meta">${p.location}</div>
        </li>
      `).join('')}
    </ul>
  `;
  
  container.querySelectorAll('.list-item').forEach(item => {
    item.addEventListener('click', () => onSelect?.(item.dataset.id));
  });
}
