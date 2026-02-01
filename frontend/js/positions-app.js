import { isAuthenticated } from './auth/store.js';
import { logout } from './api/auth.js';
import { initChatWidget } from './views/chatWidget.js';

if (!isAuthenticated()) {
  window.location.href = 'login.html';
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

async function initApp() {
  const listContainer = document.getElementById('position-list');
  const detailContainer = document.getElementById('position-detail');
  
  listContainer.innerHTML = '<div class="empty-state">Positions page - functionality to be implemented</div>';
  detailContainer.innerHTML = '<div class="empty-state">Select a position to view details</div>';
}

initApp();
setupLogout();
initChatWidget();
