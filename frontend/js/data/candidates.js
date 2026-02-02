/**
 * Candidates data layer - API backed
 * Fetches from backend, caches locally, keeps same function signatures
 */

import { api } from '../api/client.js';

// Status constants
export const CandidateStatus = {
  ACTIVE: 'active',
  ARCHIVED: 'archived',
  HIRED: 'hired',
  REJECTED: 'rejected'
};

// In-memory cache
let candidatesCache = [];
let isLoaded = false;

/**
 * Load candidates from API - call at app startup
 */
export async function loadCandidates() {
  const response = await api.get('/candidates');
  candidatesCache = response.candidates || [];
  isLoaded = true;
  return candidatesCache;
}

export function isCandidatesLoaded() {
  return isLoaded;
}

export function getAllCandidates() {
  return candidatesCache;
}

export function getActiveCandidates() {
  return candidatesCache.filter(c => c.status === CandidateStatus.ACTIVE);
}

export function getCandidateById(id) {
  return candidatesCache.find(c => c.id === id) || null;
}

export function getCandidatesByPosition(positionId) {
  return candidatesCache.filter(c => 
    c.positionIds && c.positionIds.includes(positionId)
  );
}

export function searchCandidates(query, filters = {}) {
  let results = [...candidatesCache];
  
  if (query) {
    const q = query.toLowerCase();
    results = results.filter(c => 
      c.name.toLowerCase().includes(q) ||
      (c.title && c.title.toLowerCase().includes(q))
    );
  }
  
  if (filters.status) {
    results = results.filter(c => c.status === filters.status);
  }
  
  if (filters.positionId) {
    results = results.filter(c => 
      c.positionIds && c.positionIds.includes(filters.positionId)
    );
  }
  
  return results;
}

// Local-only mutations (no backend support yet)
export async function addPositionToCandidate(candidateId, positionId) {
  await api.post(`/candidates/${candidateId}/positions/${positionId}`);
  await loadCandidates();
  return true;
}

export async function removePositionFromCandidate(candidateId, positionId) {
  await api.delete(`/candidates/${candidateId}/positions/${positionId}`);
  await loadCandidates();
  return true;
}
