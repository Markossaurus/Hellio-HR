import { renderPositionList, renderPositionDetail, filterPositionList } from './views/positionList.js';

const state = {
  selectedPositionId: null
};

function init() {
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

document.addEventListener('DOMContentLoaded', init);
