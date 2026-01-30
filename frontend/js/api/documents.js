import { getToken } from '../auth/store.js';
import { API_BASE_URL } from '../config.js';

export async function downloadCv(documentId) {
  const token = getToken();
  
  const response = await fetch(`${API_BASE_URL}/cv-documents/${documentId}/download`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (!response.ok) {
    throw new Error('Failed to download document');
  }
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  
  const contentDisposition = response.headers.get('Content-Disposition');
  let filename = 'cv.pdf';
  if (contentDisposition) {
    const match = contentDisposition.match(/filename="?([^"]+)"?/);
    if (match) filename = match[1];
  }
  
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

export async function viewCv(documentId) {
  const token = getToken();
  
  const response = await fetch(`${API_BASE_URL}/cv-documents/${documentId}/download`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (!response.ok) {
    throw new Error('Failed to load document');
  }
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  window.open(url, '_blank');
}

export async function uploadCv(file) {
  const token = getToken();
  
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to upload CV');
  }
  
  return await response.json();
}

export async function ingestDocument(documentId, forceReingest = false) {
  const token = getToken();
  
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/ingest`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ force_reingest: forceReingest })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to ingest document');
  }
  
  return await response.json();
}
