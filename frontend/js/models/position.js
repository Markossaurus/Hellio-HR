/**
 * Position (Job) data model
 * Pure data structure - no UI logic
 */

import { PositionStatus } from '../data/positions.js';

export { PositionStatus };

/**
 * Schema for position data
 */
export const PositionSchema = {
  id: 'string',
  status: 'PositionStatus',
  
  // Basic info
  title: 'string',
  department: 'string',
  location: 'string',
  type: 'string',         // full-time, part-time, contract
  
  // Description
  summary: 'string',
  responsibilities: ['string'],
  requirements: ['string'],
  niceToHave: ['string'],
  
  // Compensation (optional)
  salaryRange: {
    min: 'number',
    max: 'number',
    currency: 'string'
  },
  
  // Metadata
  createdAt: 'string',
  updatedAt: 'string',
  closedAt: 'string'
};

/**
 * Create a new position object with defaults
 */
export function createPosition(data = {}) {
  return {
    id: data.id || crypto.randomUUID(),
    status: data.status || PositionStatus.OPEN,
    title: data.title || '',
    department: data.department || '',
    location: data.location || '',
    type: data.type || 'full-time',
    summary: data.summary || '',
    responsibilities: data.responsibilities || [],
    requirements: data.requirements || [],
    niceToHave: data.niceToHave || [],
    salaryRange: data.salaryRange || null,
    createdAt: data.createdAt || new Date().toISOString(),
    updatedAt: data.updatedAt || new Date().toISOString(),
    closedAt: data.closedAt || null
  };
}

/**
 * Validate position data structure
 */
export function validatePosition(position) {
  const required = ['id', 'title', 'status'];
  const missing = required.filter(field => !position[field]);
  return { valid: missing.length === 0, missing };
}
