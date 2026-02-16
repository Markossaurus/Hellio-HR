import { getCandidateById } from '../data/candidates.js';
import { getPositionById } from '../data/positions.js';
import { downloadCv, viewCv } from '../api/documents.js';
import { getCandidateSuggestions } from '../api/suggestions.js';

const CANDIDATE_SUGGESTIONS_CACHE_KEY = 'hellio_candidate_suggestions_cache_v1';
const suggestionCacheByCandidateId = loadSuggestionCache(CANDIDATE_SUGGESTIONS_CACHE_KEY);

export function renderCandidateProfile(container, candidateId, { onAddPosition, onRemovePosition }) {
  const candidate = getCandidateById(candidateId);
  
  if (!candidate) {
    container.innerHTML = `<div class="empty-state">Select a candidate to view their profile</div>`;
    return;
  }
  
  const positions = candidate.positionIds.map(id => getPositionById(id)).filter(Boolean);
  
  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <div>
          <h2 class="card-title">${candidate.name}</h2>
          <div class="candidate-title">${candidate.title}</div>
        </div>
        ${candidate.cvDocument && candidate.cvDocument.id ? `
          <div class="cv-actions">
            <button class="btn btn-secondary cv-view-btn" data-cv-id="${candidate.cvDocument.id}">
              View CV
            </button>
            <button class="btn btn-primary cv-download-btn" data-cv-id="${candidate.cvDocument.id}">
              Download CV
            </button>
          </div>
        ` : candidate.cvDocument ? `
          <a href="${candidate.cvDocument.path}" target="_blank" class="cv-link">
            📄 View CV
          </a>
        ` : ''}
      </div>
      
      <div class="profile-section">
        <h3>Contact</h3>
        <div class="text-sm">${candidate.email || '—'}</div>
        <div class="text-sm">${candidate.phone || '—'}</div>
        <div class="text-sm">${candidate.location || '—'}</div>
      </div>
      
      ${candidate.summary ? `
        <div class="profile-section">
          <h3>Summary</h3>
          <p class="text-sm">${candidate.summary}</p>
        </div>
      ` : ''}
      
      <div class="profile-section">
        <h3>Skills</h3>
        <div class="skills">
          ${candidate.skills.length > 0 
            ? candidate.skills.map(s => `<span class="skill-tag">${s.name}</span>`).join('')
            : '<span class="text-muted text-sm">No skills listed</span>'
          }
        </div>
      </div>
      
      <div class="profile-section">
        <h3>Experience</h3>
        ${candidate.experience.length > 0 
          ? candidate.experience.map(exp => `
            <div class="timeline-item">
              <div class="timeline-title">${exp.title}</div>
              <div class="timeline-subtitle">${exp.company}</div>
              <div class="timeline-date">${formatDateRange(exp.startDate, exp.endDate)}</div>
            </div>
          `).join('')
          : '<span class="text-muted text-sm">No experience listed</span>'
        }
      </div>
      
      <div class="profile-section">
        <h3>Education</h3>
        ${candidate.education.length > 0 
          ? candidate.education.map(edu => `
            <div class="timeline-item">
              <div class="timeline-title">${edu.degree} in ${edu.field}</div>
              <div class="timeline-subtitle">${edu.institution}</div>
              <div class="timeline-date">${formatDateRange(edu.startDate, edu.endDate)}</div>
            </div>
          `).join('')
          : '<span class="text-muted text-sm">No education listed</span>'
        }
      </div>
      
      <div class="profile-section">
        <h3>Applied Positions</h3>
        <div id="position-list">
          ${positions.length > 0 
            ? positions.map(p => `
              <div class="flex" style="justify-content: space-between; align-items: center; padding: 0.5rem 0;">
                <span class="text-sm">${p.title}</span>
                <button class="btn btn-sm btn-outline btn-remove-position" data-position-id="${p.id}">Remove</button>
              </div>
            `).join('')
            : '<span class="text-muted text-sm">No positions assigned</span>'
          }
        </div>
        <button class="btn btn-sm btn-outline mt-1" id="btn-add-position">+ Add Position</button>
      </div>

      <div class="profile-section" id="candidate-suggestions-section" data-candidate-id="${candidateId}">
        <h3>Suggested Positions</h3>
        <p class="text-sm text-muted">Run AI suggestions only when needed.</p>
        ${renderCandidateSuggestionControls({ showSuggest: true, showRefresh: false })}
      </div>
    </div>
  `;

  bindCandidateSuggestionButtons(container, candidateId);
  
  container.querySelector('#btn-add-position')?.addEventListener('click', () => {
    onAddPosition?.(candidateId);
  });
  
  container.querySelectorAll('.btn-remove-position').forEach(btn => {
    btn.addEventListener('click', () => {
      onRemovePosition?.(candidateId, btn.dataset.positionId);
    });
  });

  container.querySelectorAll('.cv-view-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const cvId = e.target.dataset.cvId;
      try {
        const originalText = e.target.innerText;
        e.target.innerText = 'Opening...';
        e.target.disabled = true;
        
        await viewCv(cvId);
      } catch (error) {
        alert('Failed to open CV');
        console.error(error);
      } finally {
        e.target.innerText = originalText;
        e.target.disabled = false;
      }
    });
  });
  
  container.querySelectorAll('.cv-download-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const cvId = e.target.dataset.cvId;
      try {
        const originalText = e.target.innerText;
        e.target.innerText = 'Downloading...';
        e.target.disabled = true;

        await downloadCv(cvId);
      } catch (error) {
        alert('Failed to download CV');
        console.error(error);
      } finally {
        e.target.innerText = originalText;
        e.target.disabled = false;
      }
    });
  });
}

async function loadCandidateSuggestions(container, candidateId, options = {}) {
  const { forceRefresh = false } = options;
  const suggestionsContainer = container.querySelector('#candidate-suggestions-section');
  if (!suggestionsContainer) return;

  if (!forceRefresh && suggestionCacheByCandidateId.has(candidateId)) {
    renderCandidateSuggestionList(suggestionsContainer, suggestionCacheByCandidateId.get(candidateId));
    bindCandidateSuggestionButtons(container, candidateId);
    return;
  }

  suggestionsContainer.innerHTML = `
    <h3>Suggested Positions</h3>
    <p class="text-sm text-muted">Finding relevant positions...</p>
    ${renderCandidateSuggestionControls({ showSuggest: true, showRefresh: false, disabled: true })}
  `;

  try {
    const { suggestions } = await getCandidateSuggestions(candidateId);
    suggestionCacheByCandidateId.set(candidateId, suggestions || []);
    persistSuggestionCache(CANDIDATE_SUGGESTIONS_CACHE_KEY, suggestionCacheByCandidateId);
    const latestSuggestionsContainer = container.querySelector('#candidate-suggestions-section');

    if (!latestSuggestionsContainer || latestSuggestionsContainer.dataset.candidateId !== candidateId) {
      return;
    }

    renderCandidateSuggestionList(latestSuggestionsContainer, suggestions || []);
    bindCandidateSuggestionButtons(container, candidateId);
  } catch (error) {
    console.error('Error loading candidate suggestions:', error);
    const latestSuggestionsContainer = container.querySelector('#candidate-suggestions-section');
    if (!latestSuggestionsContainer || latestSuggestionsContainer.dataset.candidateId !== candidateId) {
      return;
    }

    latestSuggestionsContainer.innerHTML = `
      <h3>Suggested Positions</h3>
      <p class="text-sm text-muted error">Unable to load suggestions</p>
      ${renderCandidateSuggestionControls({ showSuggest: true, showRefresh: false })}
    `;
    bindCandidateSuggestionButtons(container, candidateId);
  }
}

function renderCandidateSuggestionList(container, suggestions) {
  if (!suggestions || suggestions.length === 0) {
    container.innerHTML = `
      <h3>Suggested Positions</h3>
      <p class="text-sm text-muted">No relevant positions found</p>
      ${renderCandidateSuggestionControls({ showSuggest: true, showRefresh: false })}
    `;
    return;
  }

  container.innerHTML = `
    <h3>Suggested Positions</h3>
    <div class="suggestions-list">
      ${suggestions.slice(0, 3).map((suggestion) => `
        <div class="card mb-2" style="border: 1px solid #eee; padding: 1rem;">
          <div class="candidate-name">${suggestion.title}</div>
          ${suggestion.department ? `<div class="candidate-title">${suggestion.department}</div>` : ''}
          <div class="text-sm text-muted">Match score: ${formatSimilarityScore(suggestion.similarityScore)}</div>
          <div class="mt-2 text-sm text-muted bg-gray-50 p-2 rounded">
            <strong>Why:</strong> ${suggestion.explanation}
          </div>
        </div>
      `).join('')}
    </div>
    ${renderCandidateSuggestionControls({ showSuggest: false, showRefresh: true, withMarginTop: true })}
  `;
}

function renderCandidateSuggestionControls({ showSuggest, showRefresh, disabled = false, withMarginTop = false }) {
  const buttons = [];
  const disabledAttr = disabled ? ' disabled' : '';

  if (showSuggest) {
    buttons.push(`<button class="btn btn-sm btn-outline" id="btn-load-candidate-suggestions"${disabledAttr}>Suggest Positions</button>`);
  }

  if (showRefresh) {
    buttons.push(`<button class="btn btn-sm btn-outline" id="btn-refresh-candidate-suggestions"${disabledAttr}>Refresh Suggestions</button>`);
  }

  if (buttons.length === 0) return '';

  return `<div class="flex" style="gap: 0.5rem;${withMarginTop ? ' margin-top: 0.75rem;' : ''}">${buttons.join('')}</div>`;
}

function bindCandidateSuggestionButtons(container, candidateId) {
  container.querySelector('#btn-load-candidate-suggestions')?.addEventListener('click', () => {
    loadCandidateSuggestions(container, candidateId);
  });

  container.querySelector('#btn-refresh-candidate-suggestions')?.addEventListener('click', () => {
    suggestionCacheByCandidateId.delete(candidateId);
    persistSuggestionCache(CANDIDATE_SUGGESTIONS_CACHE_KEY, suggestionCacheByCandidateId);
    loadCandidateSuggestions(container, candidateId, { forceRefresh: true });
  });
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

function formatDateRange(start, end) {
  const startStr = start || '?';
  const endStr = end === 'present' ? 'Present' : (end || '?');
  return `${startStr} – ${endStr}`;
}

function formatSimilarityScore(score) {
  const numericScore = Number(score);
  if (!Number.isFinite(numericScore)) return 'N/A';
  return `${numericScore.toFixed(1)}/10`;
}
