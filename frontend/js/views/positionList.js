import { getOpenPositions, getPositionById, searchPositions } from '../data/positions.js';
import { getCandidatesByPosition, addPositionToCandidate } from '../data/candidates.js';
import { getPositionSuggestions } from '../api/suggestions.js';

const POSITION_SUGGESTIONS_CACHE_KEY = 'hellio_position_suggestions_cache_v1';
const suggestionCacheByPositionId = loadSuggestionCache(POSITION_SUGGESTIONS_CACHE_KEY);

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
        <p class="text-sm text-muted">Run AI suggestions only when needed.</p>
        ${renderPositionSuggestionControls({ showSuggest: true, showRefresh: false })}
      </div>
    </div>
  `;

  bindSuggestionActionButtons(container, positionId);
}

async function loadSuggestions(container, positionId, options = {}) {
  const { forceRefresh = false } = options;
  const suggestionsContainer = container.querySelector('#suggestions-section');
  if (!suggestionsContainer) return;

  if (!forceRefresh && suggestionCacheByPositionId.has(positionId)) {
    renderSuggestionList(container, suggestionsContainer, positionId, suggestionCacheByPositionId.get(positionId));
    return;
  }

  suggestionsContainer.innerHTML = `
    <h3>Candidate Suggestions</h3>
    <div class="text-sm text-muted">Finding matching candidates... <span class="spinner"></span></div>
    ${renderPositionSuggestionControls({ showSuggest: true, showRefresh: false, disabled: true, withMarginTop: true })}
  `;

  try {
    const { suggestions } = await getPositionSuggestions(positionId);
    suggestionCacheByPositionId.set(positionId, suggestions || []);
    persistSuggestionCache(POSITION_SUGGESTIONS_CACHE_KEY, suggestionCacheByPositionId);
    
    // Check if we're still on the same view
    if (!container.querySelector(`#suggestions-section`)) return;

    renderSuggestionList(container, suggestionsContainer, positionId, suggestions || []);

  } catch (error) {
    console.error('Error loading suggestions:', error);
    if (container.querySelector(`#suggestions-section`)) {
      suggestionsContainer.innerHTML = `
        <h3>Candidate Suggestions</h3>
        <p class="text-sm text-muted error">Unable to load suggestions</p>
        ${renderPositionSuggestionControls({ showSuggest: true, showRefresh: false })}
      `;
      bindSuggestionActionButtons(container, positionId);
    }
  }
}

function renderSuggestionList(container, suggestionsContainer, positionId, suggestions) {
  if (!suggestions || suggestions.length === 0) {
    suggestionsContainer.innerHTML = `
      <h3>Candidate Suggestions</h3>
      <p class="text-sm text-muted">No matching candidates found</p>
      ${renderPositionSuggestionControls({ showSuggest: true, showRefresh: false })}
    `;
    bindSuggestionActionButtons(container, positionId);
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
              <div class="text-sm text-muted">Match score: ${formatSimilarityScore(s.similarityScore)}</div>
            </div>
            <button class="btn btn-sm btn-outline btn-add-candidate" data-candidate-id="${s.candidateId || s.id}">
              Add to Position
            </button>
          </div>
          <div class="mt-2 text-sm text-muted bg-gray-50 p-2 rounded">
            <strong>Why:</strong> ${s.explanation}
          </div>
        </div>
      `).join('')}
    </div>
    ${renderPositionSuggestionControls({ showSuggest: false, showRefresh: true, withMarginTop: true })}
  `;

  bindSuggestionActionButtons(container, positionId);

  suggestionsContainer.querySelectorAll('.btn-add-candidate').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const candidateId = e.target.dataset.candidateId;
      const originalText = e.target.innerText;
      
      try {
        e.target.innerText = 'Adding...';
        e.target.disabled = true;
        
        await addPositionToCandidate(candidateId, positionId);
        suggestionCacheByPositionId.delete(positionId);
        persistSuggestionCache(POSITION_SUGGESTIONS_CACHE_KEY, suggestionCacheByPositionId);

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
}

function bindSuggestionActionButtons(container, positionId) {
  container.querySelector('#btn-load-position-suggestions')?.addEventListener('click', () => {
    loadSuggestions(container, positionId);
  });

  container.querySelector('#btn-refresh-position-suggestions')?.addEventListener('click', () => {
    suggestionCacheByPositionId.delete(positionId);
    persistSuggestionCache(POSITION_SUGGESTIONS_CACHE_KEY, suggestionCacheByPositionId);
    loadSuggestions(container, positionId, { forceRefresh: true });
  });
}

function renderPositionSuggestionControls({ showSuggest, showRefresh, disabled = false, withMarginTop = false }) {
  const buttons = [];
  const disabledAttr = disabled ? ' disabled' : '';

  if (showSuggest) {
    buttons.push(`<button class="btn btn-sm btn-outline" id="btn-load-position-suggestions"${disabledAttr}>Suggest Candidates</button>`);
  }

  if (showRefresh) {
    buttons.push(`<button class="btn btn-sm btn-outline" id="btn-refresh-position-suggestions"${disabledAttr}>Refresh Suggestions</button>`);
  }

  if (buttons.length === 0) return '';

  return `<div class="flex" style="gap: 0.5rem;${withMarginTop ? ' margin-top: 0.75rem;' : ''}">${buttons.join('')}</div>`;
}

function loadSuggestionCache(storageKey) {
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw) return new Map();

    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return new Map();

    return new Map(parsed.filter((entry) => Array.isArray(entry) && entry.length === 2));
  } catch {
    return new Map();
  }
}

function persistSuggestionCache(storageKey, cacheMap) {
  try {
    localStorage.setItem(storageKey, JSON.stringify(Array.from(cacheMap.entries())));
  } catch {
  }
}

function formatCurrency(amount, currency = 'USD') {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency, maximumFractionDigits: 0 }).format(amount);
}

function formatSimilarityScore(score) {
  const numericScore = Number(score);
  if (!Number.isFinite(numericScore)) return 'N/A';
  return `${numericScore.toFixed(1)}/10`;
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
