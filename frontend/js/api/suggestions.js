import { api } from './client.js';

export async function getPositionSuggestions(positionId) {
    return api.get(`/positions/${positionId}/suggestions`);
}

export async function getCandidateSuggestions(candidateId) {
    return api.get(`/candidates/${candidateId}/suggestions`);
}
