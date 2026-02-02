import { isAuthenticated } from './auth/store.js';
import { logout } from './api/auth.js';
import { loadPositions } from './data/positions.js';
import { loadCandidates } from './data/candidates.js';
import { renderPositionList, renderPositionDetail, filterPositionList } from './views/positionList.js';
import { initChatWidget } from './views/chatWidget.js';

if (!isAuthenticated()) {
  window.location.href = 'login.html';
}

const state = {
  selectedPositionId: null
};

function setupLogout() {
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      logout();
    });
  }
}

async function initApp() {
  const listContainer = document.getElementById('position-list');
  const detailContainer = document.getElementById('position-detail');
  const searchInput = document.getElementById('search-input');

  try {
    showLoading();
    await Promise.all([
      loadPositions(),
      loadCandidates()
    ]);
    hideLoading();

    renderPositionList(listContainer, {
      onSelect: selectPosition,
      selectedId: state.selectedPositionId
    });

    renderPositionDetail(detailContainer, state.selectedPositionId);

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
    console.error('Failed to initialize positions page:', error);
    if (error.message === 'Unauthorized') {
      window.location.href = 'login.html';
    } else {
      showError('Failed to load positions. Please try again.');
    }
  }
}

function selectPosition(positionId) {
  state.selectedPositionId = positionId;

  const listContainer = document.getElementById('position-list');
  const detailContainer = document.getElementById('position-detail');

  renderPositionList(listContainer, {
    onSelect: selectPosition,
    selectedId: state.selectedPositionId
  });

  renderPositionDetail(detailContainer, state.selectedPositionId);
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

initApp();
setupLogout();
initChatWidget();
