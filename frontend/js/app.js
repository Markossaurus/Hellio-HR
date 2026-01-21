import { renderCandidateList, filterCandidateList } from './views/candidateList.js';
import { renderCandidateProfile } from './views/candidateProfile.js';
import { renderCandidateCompare } from './views/candidateCompare.js';
import { getActiveCandidates, addPositionToCandidate, removePositionFromCandidate } from './data/candidates.js';
import { getOpenPositions } from './data/positions.js';

const state = {
  selectedCandidateId: null,
  compareIds: [null, null],
  view: 'list'
};

function init() {
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

document.addEventListener('DOMContentLoaded', init);
