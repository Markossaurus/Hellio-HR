/**
 * Positions page entry point
 */

import { isAuthenticated } from './auth/store.js';
import { logout } from './api/auth.js';
import { loadPositions } from './data/positions.js';
import { loadCandidates } from './data/candidates.js';
import { renderPositionList, renderPositionDetail, filterPositionList } from './views/positionList.js';

if (!isAuthenticated()) {
  window.location.href = 'login.html';
}

const state = {
  selectedPositionId: null
};

async function initPositionsApp() {
  try {
    showLoading();
    
    await Promise.all([
      loadPositions(),
      loadCandidates()  // Need candidates for position detail view
    ]);
    
    hideLoading();
    
    const listContainer = document.getElementById('position-list');
    const detailContainer = document.getElementById('position-detail');
    const searchInput = document.getElementById('search-input');
    
    renderPositionList(listContainer, {
      onSelect: selectPosition,
      selectedId: state.selectedPositionId
    });
    
    renderPositionDetail(detailContainer, null);
    
    searchInput?.addEventListener('input', (e) => {
      const query = e.target.value.trim();
      if (query) {
        filterPositionList(listContainer, query, {
          onSelect: selectPosition,
          selectedId: state.selectedPositionId
        });
      } else {
        renderPositionList(listContainer, {
          onSelect: selectPosition,
          selectedId: state.selectedPositionId
        });
      }
    });
    
  } catch (error) {
    console.error('Failed to initialize positions app:', error);
    if (error.message === 'Unauthorized') {
      window.location.href = 'login.html';
    } else {
      showError('Failed to load data. Please try again.');
    }
  }
}

function showLoading() {
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

function setupLogout() {
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      logout();
    });
  }
}

function selectPosition(id) {
  state.selectedPositionId = id;
  
  const listContainer = document.getElementById('position-list');
  const detailContainer = document.getElementById('position-detail');
  
  renderPositionList(listContainer, {
    onSelect: selectPosition,
    selectedId: id
  });
  
  renderPositionDetail(detailContainer, id);
}

document.addEventListener('DOMContentLoaded', () => {
  initPositionsApp();
  setupLogout();
});
