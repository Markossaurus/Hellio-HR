/**
 * Candidate data model
 * Pure data structure - no UI logic
 */

export const CandidateStatus = {
  ACTIVE: 'active',
  ARCHIVED: 'archived',
  HIRED: 'hired',
  REJECTED: 'rejected'
};

/**
 * Schema for candidate data
 * All lists use stable IDs for comparison/tracking
 */
export const CandidateSchema = {
  id: 'string',           // Unique identifier
  status: 'CandidateStatus',
  
  // Basic info
  name: 'string',
  email: 'string',
  phone: 'string',
  location: 'string',
  title: 'string',        // Current/desired job title
  summary: 'string',      // Brief professional summary
  
  // Normalized lists with stable IDs
  skills: [{ id: 'string', name: 'string', level: 'string' }],
  experience: [{
    id: 'string',
    company: 'string',
    title: 'string',
    startDate: 'string',  // YYYY-MM format
    endDate: 'string',    // YYYY-MM or 'present'
    description: 'string'
  }],
  education: [{
    id: 'string',
    institution: 'string',
    degree: 'string',
    field: 'string',
    startDate: 'string',
    endDate: 'string'
  }],
  
  // Position associations
  positionIds: ['string'],
  
  // Document references
  cvDocument: {
    filename: 'string',
    path: 'string',
    uploadedAt: 'string'
  },
  
  // Metadata
  createdAt: 'string',
  updatedAt: 'string'
};

/**
 * Create a new candidate object with defaults
 */
export function createCandidate(data = {}) {
  return {
    id: data.id || crypto.randomUUID(),
    status: data.status || CandidateStatus.ACTIVE,
    name: data.name || '',
    email: data.email || '',
    phone: data.phone || '',
    location: data.location || '',
    title: data.title || '',
    summary: data.summary || '',
    skills: data.skills || [],
    experience: data.experience || [],
    education: data.education || [],
    positionIds: data.positionIds || [],
    cvDocument: data.cvDocument || null,
    createdAt: data.createdAt || new Date().toISOString(),
    updatedAt: data.updatedAt || new Date().toISOString()
  };
}

/**
 * Validate candidate data structure
 */
export function validateCandidate(candidate) {
  const required = ['id', 'name', 'status'];
  const missing = required.filter(field => !candidate[field]);
  return { valid: missing.length === 0, missing };
}
