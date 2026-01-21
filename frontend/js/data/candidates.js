/**
 * Mock candidate data
 * Replace with API calls in future stages
 */

import { CandidateStatus } from '../models/candidate.js';

export const candidates = [
  {
    id: 'cand-001',
    status: CandidateStatus.ACTIVE,
    name: 'Sarah Chen',
    email: 'sarah.chen@email.com',
    phone: '+1-415-555-0142',
    location: 'San Francisco, CA',
    title: 'Senior Full-Stack Engineer',
    summary: 'Results-driven engineer with 7+ years building scalable web applications. Led teams of 5-8 developers. Strong focus on performance optimization and clean architecture.',
    skills: [
      { id: 'sk-001', name: 'TypeScript', level: 'expert' },
      { id: 'sk-002', name: 'React', level: 'expert' },
      { id: 'sk-003', name: 'Node.js', level: 'advanced' },
      { id: 'sk-004', name: 'PostgreSQL', level: 'advanced' },
      { id: 'sk-005', name: 'AWS', level: 'intermediate' },
      { id: 'sk-006', name: 'GraphQL', level: 'advanced' }
    ],
    experience: [
      {
        id: 'exp-001',
        company: 'Stripe',
        title: 'Senior Software Engineer',
        startDate: '2021-03',
        endDate: 'present',
        description: 'Lead frontend architect for payment dashboard. Reduced page load time by 40%.'
      },
      {
        id: 'exp-002',
        company: 'Airbnb',
        title: 'Software Engineer',
        startDate: '2018-06',
        endDate: '2021-02',
        description: 'Built search infrastructure components. Mentored 3 junior engineers.'
      },
      {
        id: 'exp-003',
        company: 'Startup Labs',
        title: 'Junior Developer',
        startDate: '2016-08',
        endDate: '2018-05',
        description: 'Full-stack development for e-commerce platform.'
      }
    ],
    education: [
      {
        id: 'edu-001',
        institution: 'UC Berkeley',
        degree: 'B.S.',
        field: 'Computer Science',
        startDate: '2012-09',
        endDate: '2016-05'
      }
    ],
    positionIds: ['pos-001', 'pos-002'],
    cvDocument: null,
    createdAt: '2024-01-10T09:30:00Z',
    updatedAt: '2024-01-15T14:20:00Z'
  },
  {
    id: 'cand-002',
    status: CandidateStatus.ACTIVE,
    name: 'Marcus Johnson',
    email: 'marcus.j@email.com',
    phone: '+1-512-555-0198',
    location: 'Austin, TX (Remote)',
    title: 'Backend Engineer',
    summary: 'Passionate about distributed systems and API design. 5 years of experience in high-traffic environments. Open source contributor.',
    skills: [
      { id: 'sk-010', name: 'Python', level: 'expert' },
      { id: 'sk-011', name: 'Go', level: 'advanced' },
      { id: 'sk-012', name: 'Kubernetes', level: 'advanced' },
      { id: 'sk-013', name: 'PostgreSQL', level: 'expert' },
      { id: 'sk-014', name: 'Redis', level: 'advanced' },
      { id: 'sk-015', name: 'gRPC', level: 'intermediate' }
    ],
    experience: [
      {
        id: 'exp-010',
        company: 'Datadog',
        title: 'Backend Engineer',
        startDate: '2022-01',
        endDate: 'present',
        description: 'Building metrics ingestion pipeline handling 2M events/sec.'
      },
    ],
    education: [
      {
        id: 'edu-010',
        institution: 'University of Texas',
        degree: 'M.S.',
        field: 'Computer Science',
        startDate: '2017-09',
        endDate: '2019-05'
      },
      {
        id: 'edu-011',
        institution: 'Texas A&M',
        degree: 'B.S.',
        field: 'Software Engineering',
        startDate: '2013-09',
        endDate: '2017-05'
      }
    ],
    positionIds: ['pos-002'],
    cvDocument: null,
    createdAt: '2024-01-12T11:00:00Z',
    updatedAt: '2024-01-12T11:00:00Z'
  },
  {
    id: 'cand-003',
    status: CandidateStatus.ACTIVE,
    name: 'Elena Rodriguez',
    email: 'elena.r@email.com',
    phone: '+1-646-555-0167',
    location: 'New York, NY',
    title: 'Product Designer & Frontend Developer',
    summary: 'Hybrid designer-developer with 6 years crafting user experiences. Figma expert. Strong in design systems, accessibility, and React implementation.',
    skills: [
      { id: 'sk-020', name: 'Figma', level: 'expert' },
      { id: 'sk-021', name: 'React', level: 'advanced' },
      { id: 'sk-022', name: 'CSS/Tailwind', level: 'expert' },
      { id: 'sk-023', name: 'TypeScript', level: 'intermediate' },
      { id: 'sk-024', name: 'User Research', level: 'advanced' },
      { id: 'sk-025', name: 'Accessibility', level: 'advanced' }
    ],
    experience: [
      {
        id: 'exp-020',
        company: 'Figma',
        title: 'Product Designer',
        startDate: '2022-06',
        endDate: 'present',
        description: 'Design systems team. Shipped component library used by 200+ designers.'
      },
      {
        id: 'exp-021',
        company: 'Shopify',
        title: 'UX Engineer',
        startDate: '2019-03',
        endDate: '2022-05',
        description: 'Bridged design and engineering. Built Polaris components.'
      },
      {
        id: 'exp-022',
        company: 'Agency Co',
        title: 'UI Designer',
        startDate: '2017-06',
        endDate: '2019-02',
        description: 'Client-facing design work for Fortune 500 companies.'
      }
    ],
    education: [
      {
        id: 'edu-020',
        institution: 'Parsons School of Design',
        degree: 'B.F.A.',
        field: 'Design & Technology',
        startDate: '2013-09',
        endDate: '2017-05'
      }
    ],
    positionIds: ['pos-001'],
    cvDocument: null,
    createdAt: '2024-01-14T16:45:00Z',
    updatedAt: '2024-01-14T16:45:00Z'
  }
];

/**
 * Data access functions
 * These will be replaced with API calls later
 */

export function getAllCandidates() {
  return candidates;
}

export function getActiveCandidates() {
  return candidates.filter(c => c.status === CandidateStatus.ACTIVE);
}

export function getCandidateById(id) {
  return candidates.find(c => c.id === id) || null;
}

export function getCandidatesByPosition(positionId) {
  return candidates.filter(c => c.positionIds.includes(positionId));
}

export function searchCandidates(query, filters = {}) {
  let results = [...candidates];
  
  // Text search (name, title)
  if (query) {
    const q = query.toLowerCase();
    results = results.filter(c => 
      c.name.toLowerCase().includes(q) ||
      c.title.toLowerCase().includes(q)
    );
  }
  
  // Status filter
  if (filters.status) {
    results = results.filter(c => c.status === filters.status);
  }
  
  // Position filter
  if (filters.positionId) {
    results = results.filter(c => c.positionIds.includes(filters.positionId));
  }
  
  return results;
}

/**
 * Mutation functions (in-memory only for Stage 1)
 */

export function addPositionToCandidate(candidateId, positionId) {
  const candidate = getCandidateById(candidateId);
  if (candidate && !candidate.positionIds.includes(positionId)) {
    candidate.positionIds.push(positionId);
    candidate.updatedAt = new Date().toISOString();
    return true;
  }
  return false;
}

export function removePositionFromCandidate(candidateId, positionId) {
  const candidate = getCandidateById(candidateId);
  if (candidate) {
    const idx = candidate.positionIds.indexOf(positionId);
    if (idx > -1) {
      candidate.positionIds.splice(idx, 1);
      candidate.updatedAt = new Date().toISOString();
      return true;
    }
  }
  return false;
}
