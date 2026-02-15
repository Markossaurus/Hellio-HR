import { getOpenPositions, getPositionById, searchPositions } from '../data/positions.js';
import { getCandidatesByPosition, addPositionToCandidate } from '../data/candidates.js';
import { getPositionSuggestions } from '../api/suggestions.js';

export function renderPositionList(container, { onSelect, selectedId }) {
  const positions = getOpenPositions();
  
  if (positions.length === 0) {
    container.innerHTML = `<div class="empty-state">No open positions</div>`;
    return;
  }
  
  container.innerHTML = `
    <ul class="list">
      ${positions.map(p => {
        const metaParts = [normalizeMeta(p.department), normalizeMeta(p.location)].filter(Boolean);
        const meta = metaParts.length > 0 ? metaParts.join(' • ') : '';
        return `
        <li class="list-item ${selectedId === p.id ? 'selected' : ''}" data-id="${p.id}">
          <div class="candidate-name">${p.title}</div>
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
          <div class="candidate-title">${[normalizeMeta(position.department), normalizeMeta(position.location)].filter(Boolean).join(' • ')}</div>
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

      <div class="profile-section" id="suggestions-section">
        <h3>Candidate Suggestions</h3>
        <div class="text-sm text-muted">Finding matching candidates... <span class="spinner"></span></div>
      </div>
    </div>
  `;

  // Fetch suggestions
  loadSuggestions(container, positionId);
}

async function loadSuggestions(container, positionId) {
  const suggestionsContainer = container.querySelector('#suggestions-section');
  if (!suggestionsContainer) return;

  try {
    const { suggestions } = await getPositionSuggestions(positionId);
    
    // Check if we're still on the same view
    if (!container.querySelector(`#suggestions-section`)) return;

    if (!suggestions || suggestions.length === 0) {
      suggestionsContainer.innerHTML = `
        <h3>Candidate Suggestions</h3>
        <p class="text-sm text-muted">No matching candidates found</p>
      `;
      return;
    }

    suggestionsContainer.innerHTML = `
      <h3>Candidate Suggestions</h3>
      <div class="suggestions-list">
        ${suggestions.map(s => `
          <div class="card mb-2" style="border: 1px solid #eee; padding: 1rem;">
            <div class="flex justify-between items-start">
              <div>
                <div class="candidate-name">${s.name}</div>
                <div class="candidate-title">${s.title}</div>
              </div>
              <button class="btn btn-sm btn-outline btn-add-candidate" data-candidate-id="${s.id}">
                Add to Position
              </button>
            </div>
            <div class="mt-2 text-sm text-muted bg-gray-50 p-2 rounded">
              <strong>Why:</strong> ${s.explanation}
            </div>
          </div>
        `).join('')}
      </div>
    `;

    // Add event listeners
    suggestionsContainer.querySelectorAll('.btn-add-candidate').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const candidateId = e.target.dataset.candidateId;
        const originalText = e.target.innerText;
        
        try {
          e.target.innerText = 'Adding...';
          e.target.disabled = true;
          
          await addPositionToCandidate(candidateId, positionId);
          
          // Refresh the entire detail view to show the new candidate in the list
          renderPositionDetail(container, positionId);
        } catch (error) {
          console.error('Failed to add candidate:', error);
          e.target.innerText = originalText;
          e.target.disabled = false;
          alert('Failed to add candidate to position');
        }
      });
    });

  } catch (error) {
    console.error('Error loading suggestions:', error);
    if (container.querySelector(`#suggestions-section`)) {
      suggestionsContainer.innerHTML = `
        <h3>Candidate Suggestions</h3>
        <p class="text-sm text-muted error">Unable to load suggestions</p>
      `;
    }
  }
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
      ${results.map(p => {
        const metaParts = [normalizeMeta(p.department), normalizeMeta(p.location)].filter(Boolean);
        const meta = metaParts.length > 0 ? metaParts.join(' • ') : '';
        return `
        <li class="list-item ${selectedId === p.id ? 'selected' : ''}" data-id="${p.id}">
          <div class="candidate-name">${p.title}</div>
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
