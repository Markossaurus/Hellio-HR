/**
 * Positions data layer - API backed
 */

import { api } from '../api/client.js';

export const PositionStatus = {
  OPEN: 'open',
  CLOSED: 'closed',
  ON_HOLD: 'on_hold',
  FILLED: 'filled'
};

let positionsCache = [];
let isLoaded = false;

export async function loadPositions() {
  const response = await api.get('/positions');
  positionsCache = response.positions || [];
  isLoaded = true;
  return positionsCache;
}

export function isPositionsLoaded() {
  return isLoaded;
}

export function getAllPositions() {
  return positionsCache;
}

export function getOpenPositions() {
  return positionsCache.filter(p => p.status === PositionStatus.OPEN);
}

export function getPositionById(id) {
  return positionsCache.find(p => p.id === id) || null;
}

export function searchPositions(query, filters = {}) {
  let results = [...positionsCache];
  
  if (query) {
    const q = query.toLowerCase();
    results = results.filter(p =>
      p.title.toLowerCase().includes(q) ||
      (p.department && p.department.toLowerCase().includes(q))
    );
  }
  
  if (filters.status) {
    results = results.filter(p => p.status === filters.status);
  }
  
  if (filters.department) {
    results = results.filter(p => p.department === filters.department);
  }
  
  return results;
}

export async function updatePosition(positionId, updates) {
  const response = await api.patch(`/positions/${positionId}`, updates);
  const idx = positionsCache.findIndex(p => p.id === positionId);
  if (idx !== -1) {
    positionsCache[idx] = response;
  }
  return response;
}
