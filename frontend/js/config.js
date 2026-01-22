/**
 * Frontend configuration
 * Set window.API_BASE_URL before loading app to override
 */

// Use /api prefix - nginx proxies to backend
export const API_BASE_URL = window.API_BASE_URL || '/api';

// Other config
export const APP_NAME = 'Hellio HR';
