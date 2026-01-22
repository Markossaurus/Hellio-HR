import { getToken } from '../auth/store.js';
import { API_BASE_URL } from '../config.js';

/**
 * Download a CV document
 * Opens the CV in a new tab or triggers download
 */
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
  
  // Get the blob and create download link
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  
  // Get filename from Content-Disposition header or use default
  const contentDisposition = response.headers.get('Content-Disposition');
  let filename = 'cv.pdf';
  if (contentDisposition) {
    const match = contentDisposition.match(/filename="?([^"]+)"?/);
    if (match) filename = match[1];
  }
  
  // Create temporary link and click it
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

/**
 * Open CV in new tab for viewing
 */
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
