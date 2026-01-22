/**
 * Main application entry point for candidates page
 */

import { isAuthenticated } from './auth/store.js';
import { logout } from './api/auth.js';
import { loadCandidates, getActiveCandidates, addPositionToCandidate, removePositionFromCandidate } from './data/candidates.js';
import { loadPositions, getOpenPositions } from './data/positions.js';
import { renderCandidateList, filterCandidateList } from './views/candidateList.js';
import { renderCandidateProfile } from './views/candidateProfile.js';
import { renderCandidateCompare } from './views/candidateCompare.js';

// Check auth - redirect to login if not authenticated
if (!isAuthenticated()) {
  window.location.href = 'login.html';
}

const state = {
  selectedCandidateId: null,
  compareIds: [null, null],
  view: 'list'
};

async function initApp() {
  try {
    // Show loading state
    showLoading();
    
    // Load data from API
    await Promise.all([
      loadCandidates(),
      loadPositions()
    ]);
    
    // Hide loading, render UI
    hideLoading();
    
    const listContainer = document.getElementById('candidate-list');
    const profileContainer = document.getElementById('candidate-profile');
    const compareContainer = document.getElementById('compare-container');
    const searchInput = document.getElementById('search-input');
    
    renderCandidateList(listContainer, {
      onSelect: selectCandidate,
      selectedIds: state.selectedCandidateId ? [state.selectedCandidateId] : []
    });
    
    renderCandidateProfile(profileContainer, null, {
      onAddPosition: showAddPositionModal,
      onRemovePosition: handleRemovePosition
    });
    
    populateCompareSelects();
    
    searchInput?.addEventListener('input', (e) => {
      const query = e.target.value.trim();
      if (query) {
        filterCandidateList(listContainer, query, {
          onSelect: selectCandidate,
          selectedIds: state.selectedCandidateId ? [state.selectedCandidateId] : []
        });
      } else {
        renderCandidateList(listContainer, {
          onSelect: selectCandidate,
          selectedIds: state.selectedCandidateId ? [state.selectedCandidateId] : []
        });
      }
    });
    
    document.getElementById('btn-view-list')?.addEventListener('click', () => switchView('list'));
    document.getElementById('btn-view-compare')?.addEventListener('click', () => switchView('compare'));
    
    document.getElementById('compare-select-1')?.addEventListener('change', (e) => {
      state.compareIds[0] = e.target.value || null;
      renderCandidateCompare(compareContainer, state.compareIds[0], state.compareIds[1]);
    });
    
    document.getElementById('compare-select-2')?.addEventListener('change', (e) => {
      state.compareIds[1] = e.target.value || null;
      renderCandidateCompare(compareContainer, state.compareIds[0], state.compareIds[1]);
    });
    
    const modalOverlay = document.getElementById('modal-add-position');
    modalOverlay?.querySelector('.modal-close')?.addEventListener('click', hideModal);
    modalOverlay?.addEventListener('click', (e) => {
      if (e.target === modalOverlay) hideModal();
    });
    
  } catch (error) {
    console.error('Failed to initialize app:', error);
    // If auth error, redirect to login
    if (error.message === 'Unauthorized') {
      window.location.href = 'login.html';
    } else {
      showError('Failed to load data. Please try again.');
    }
  }
}

function showLoading() {
  // Add a loading indicator to the page
  const main = document.querySelector('main') || document.body;
  const loader = document.createElement('div');
  loader.id = 'app-loader';
  loader.className = 'app-loader';
  loader.innerHTML = '<div class="loader-spinner"></div><p>Loading...</p>';
  main.prepend(loader);
}

function hideLoading() {
  const loader = document.getElementById('app-loader');
  if (loader) loader.remove();
}

function showError(message) {
  const main = document.querySelector('main') || document.body;
  main.innerHTML = `<div class="error-message">${message}</div>`;
}

// Add logout handler
function setupLogout() {
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      logout();
    });
  }
}

function selectCandidate(id) {
  state.selectedCandidateId = id;
  
  const listContainer = document.getElementById('candidate-list');
  const profileContainer = document.getElementById('candidate-profile');
  
  renderCandidateList(listContainer, {
    onSelect: selectCandidate,
    selectedIds: [id]
  });
  
  renderCandidateProfile(profileContainer, id, {
    onAddPosition: showAddPositionModal,
    onRemovePosition: handleRemovePosition
  });
}

function switchView(view) {
  state.view = view;
  
  document.getElementById('view-list')?.classList.toggle('hidden', view !== 'list');
  document.getElementById('view-compare')?.classList.toggle('hidden', view !== 'compare');
  
  document.getElementById('btn-view-list')?.classList.toggle('btn-primary', view === 'list');
  document.getElementById('btn-view-compare')?.classList.toggle('btn-primary', view === 'compare');
  
  if (view === 'compare') {
    renderCandidateCompare(
      document.getElementById('compare-container'),
      state.compareIds[0],
      state.compareIds[1]
    );
  }
}

function populateCompareSelects() {
  const candidates = getActiveCandidates();
  const options = candidates.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
  
  const select1 = document.getElementById('compare-select-1');
  const select2 = document.getElementById('compare-select-2');
  
  if (select1) select1.innerHTML = `<option value="">Select first candidate</option>${options}`;
  if (select2) select2.innerHTML = `<option value="">Select second candidate</option>${options}`;
}

function showAddPositionModal(candidateId) {
  const modal = document.getElementById('modal-add-position');
  const listContainer = document.getElementById('modal-position-list');
  
  const positions = getOpenPositions();
  
  listContainer.innerHTML = positions.length > 0
    ? `<ul class="list">
        ${positions.map(p => `
          <li class="list-item" data-position-id="${p.id}" style="cursor: pointer;">
            <div class="candidate-name">${p.title}</div>
            <div class="candidate-title">${p.department}</div>
          </li>
        `).join('')}
      </ul>`
    : '<div class="empty-state">No open positions</div>';
  
  listContainer.querySelectorAll('.list-item').forEach(item => {
    item.addEventListener('click', () => {
      addPositionToCandidate(candidateId, item.dataset.positionId);
      hideModal();
      selectCandidate(candidateId);
    });
  });
  
  modal?.classList.add('active');
}

function hideModal() {
  document.getElementById('modal-add-position')?.classList.remove('active');
}

function handleRemovePosition(candidateId, positionId) {
  removePositionFromCandidate(candidateId, positionId);
  selectCandidate(candidateId);
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  initApp();
  setupLogout();
});
