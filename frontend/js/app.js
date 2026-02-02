/**
 * Main application entry point for candidates page
 */

import { isAuthenticated } from './auth/store.js';
import { logout } from './api/auth.js';
import { uploadCv, ingestDocument } from './api/documents.js';
import { loadCandidates, getActiveCandidates, addPositionToCandidate, removePositionFromCandidate } from './data/candidates.js';
import { loadPositions, getOpenPositions } from './data/positions.js';
import { renderCandidateList, filterCandidateList } from './views/candidateList.js';
import { renderCandidateProfile } from './views/candidateProfile.js';
import { renderCandidateCompare } from './views/candidateCompare.js';
import { initChatWidget } from './views/chatWidget.js';

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
  // 1. Initialize UI event listeners that don't depend on data
  // This ensures buttons work even if API is slow
  document.getElementById('btn-upload-cv')?.addEventListener('click', showUploadModal);
  
  document.getElementById('btn-view-list')?.addEventListener('click', () => switchView('list'));
  document.getElementById('btn-view-compare')?.addEventListener('click', () => switchView('compare'));
  
  const modalOverlay = document.getElementById('modal-add-position');
  modalOverlay?.querySelector('.modal-close')?.addEventListener('click', hideModal);
  modalOverlay?.addEventListener('click', (e) => {
    if (e.target === modalOverlay) hideModal();
  });

  setupUploadModal();

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
    
    document.getElementById('compare-select-1')?.addEventListener('change', (e) => {
      state.compareIds[0] = e.target.value || null;
      renderCandidateCompare(compareContainer, state.compareIds[0], state.compareIds[1]);
    });
    
    document.getElementById('compare-select-2')?.addEventListener('change', (e) => {
      state.compareIds[1] = e.target.value || null;
      renderCandidateCompare(compareContainer, state.compareIds[0], state.compareIds[1]);
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
        ${positions.map(p => {
          const metaParts = [normalizeMeta(p.department), normalizeMeta(p.location)].filter(Boolean);
          const meta = metaParts.length > 0 ? metaParts.join(' • ') : '';
          return `
          <li class="list-item" data-position-id="${p.id}" style="cursor: pointer;">
            <div class="candidate-name">${p.title}</div>
            ${meta ? `<div class="candidate-title">${meta}</div>` : ''}
          </li>
        `;
        }).join('')}
      </ul>`
    : '<div class="empty-state">No open positions</div>';
  
  listContainer.querySelectorAll('.list-item').forEach(item => {
    item.addEventListener('click', async () => {
      await addPositionToCandidate(candidateId, item.dataset.positionId);
      hideModal();
      selectCandidate(candidateId);
    });
  });
  
  modal?.classList.add('active');
}

function hideModal() {
  document.getElementById('modal-add-position')?.classList.remove('active');
}

async function handleRemovePosition(candidateId, positionId) {
  await removePositionFromCandidate(candidateId, positionId);
  selectCandidate(candidateId);
}

function setupUploadModal() {
  const modal = document.getElementById('modal-upload-cv');
  if (!modal) return;

  // Close handlers
  modal.querySelector('.modal-close')?.addEventListener('click', () => {
    modal.classList.remove('active');
    resetUploadModal();
  });
  
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.classList.remove('active');
      resetUploadModal();
    }
  });

  // Drag and Drop
  const dropzone = document.getElementById('upload-dropzone');
  const fileInput = document.getElementById('file-upload');
  
  if (!dropzone || !fileInput) return;

  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, () => dropzone.classList.add('drag-over'), false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, () => dropzone.classList.remove('drag-over'), false);
  });

  dropzone.addEventListener('drop', handleDrop, false);
  
  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
  }

  // Click to upload
  dropzone.addEventListener('click', () => fileInput.click());
  
  fileInput.addEventListener('click', (e) => e.stopPropagation()); // Prevent bubbling back to dropzone

  fileInput.addEventListener('change', function() {
    handleFiles(this.files);
  });
}

function handleFiles(files) {
  if (files.length > 0) {
    const file = files[0];
    if (validateFile(file)) {
      uploadFile(file);
    }
  }
}

function validateFile(file) {
  const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
  if (!validTypes.includes(file.type)) {
    showUploadError('Invalid file type. Please upload PDF or DOCX.');
    return false;
  }
  if (file.size > 10 * 1024 * 1024) { // 10MB
    showUploadError('File is too large. Max size is 10MB.');
    return false;
  }
  return true;
}

function showUploadModal() {
  const modal = document.getElementById('modal-upload-cv');
  modal?.classList.add('active');
  resetUploadModal();
}

function resetUploadModal() {
  document.getElementById('upload-dropzone')?.classList.remove('hidden');
  document.getElementById('upload-progress-container')?.classList.add('hidden');
  document.getElementById('upload-result')?.classList.add('hidden');
  document.getElementById('upload-result').innerHTML = '';
  const fileInput = document.getElementById('file-upload');
  if (fileInput) fileInput.value = '';
}

async function uploadFile(file) {
  const dropzone = document.getElementById('upload-dropzone');
  const progressContainer = document.getElementById('upload-progress-container');
  const progressBar = document.getElementById('upload-progress-bar');
  const statusText = document.getElementById('upload-status-text');
  const percentage = document.getElementById('upload-percentage');
  
  dropzone.classList.add('hidden');
  progressContainer.classList.remove('hidden');
  
  try {
    // 1. Upload
    statusText.textContent = 'Uploading...';
    progressBar.style.width = '30%';
    percentage.textContent = '30%';
    
    const uploadResult = await uploadCv(file);
    
    // 2. Ingest
    statusText.textContent = 'Processing with AI...';
    progressBar.style.width = '60%';
    percentage.textContent = '60%';
    
    await ingestDocument(uploadResult.id);
    
    // 3. Success
    progressBar.style.width = '100%';
    percentage.textContent = '100%';
    statusText.textContent = 'Complete';
    
    showUploadSuccess(`Successfully added candidate from ${file.name}`);
    
    // Refresh list
    await loadCandidates();
    // Re-render list if we are in list view
    const listContainer = document.getElementById('candidate-list');
    if (listContainer) {
        renderCandidateList(listContainer, {
          onSelect: selectCandidate,
          selectedIds: state.selectedCandidateId ? [state.selectedCandidateId] : []
        });
    }

    setTimeout(() => {
        document.getElementById('modal-upload-cv')?.classList.remove('active');
    }, 2000);

  } catch (error) {
    console.error(error);
    showUploadError(error.message || 'An error occurred during upload');
    dropzone.classList.remove('hidden');
    progressContainer.classList.add('hidden');
  }
}

function showUploadSuccess(message) {
  const resultDiv = document.getElementById('upload-result');
  resultDiv.classList.remove('hidden', 'status-error');
  resultDiv.classList.add('status-message', 'status-success');
  resultDiv.innerHTML = `<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg> ${message}`;
}

function showUploadError(message) {
  const resultDiv = document.getElementById('upload-result');
  resultDiv.classList.remove('hidden', 'status-success');
  resultDiv.classList.add('status-message', 'status-error');
  resultDiv.classList.remove('hidden');
  resultDiv.innerHTML = `<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg> ${message}`;
}

function normalizeMeta(value) {
  if (!value) return '';
  if (typeof value !== 'string') return value;
  const trimmed = value.trim();
  const lowered = trimmed.toLowerCase();
  if (!trimmed || lowered === 'null' || lowered === 'undefined') return '';
  return trimmed;
}

// Initialize when module loads (deferred by default)
initApp();
setupLogout();
initChatWidget();
