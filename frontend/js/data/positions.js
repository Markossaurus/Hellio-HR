/**
 * Mock position data
 * Replace with API calls in future stages
 */

import { PositionStatus } from '../models/position.js';

export const positions = [
  {
    id: 'pos-001',
    status: PositionStatus.OPEN,
    title: 'Senior Frontend Engineer',
    department: 'Engineering',
    location: 'San Francisco, CA (Hybrid)',
    type: 'full-time',
    summary: 'Join our product team to build the next generation of HR tools. You will lead frontend architecture decisions and mentor junior developers while shipping features that impact millions of users.',
    responsibilities: [
      'Architect and implement complex React applications',
      'Collaborate with designers to deliver pixel-perfect UIs',
      'Mentor team members through code reviews and pairing',
      'Drive technical decisions and best practices',
      'Optimize application performance and accessibility'
    ],
    requirements: [
      '5+ years of frontend development experience',
      'Expert-level TypeScript and React skills',
      'Experience with state management (Redux, Zustand, etc.)',
      'Strong understanding of web performance optimization',
      'Excellent communication skills'
    ],
    niceToHave: [
      'Experience building design systems',
      'Familiarity with Node.js or Python backends',
      'Contributions to open source projects'
    ],
    salaryRange: { min: 160000, max: 210000, currency: 'USD' },
    createdAt: '2024-01-05T00:00:00Z',
    updatedAt: '2024-01-05T00:00:00Z',
    closedAt: null
  },
  {
    id: 'pos-002',
    status: PositionStatus.OPEN,
    title: 'Staff Backend Engineer',
    department: 'Engineering',
    location: 'Remote (US)',
    type: 'full-time',
    summary: 'We are scaling our platform to handle 10x growth. Looking for a seasoned backend engineer to design distributed systems, optimize database performance, and establish engineering standards.',
    responsibilities: [
      'Design and build scalable microservices',
      'Own critical infrastructure components',
      'Lead technical design reviews',
      'Establish monitoring and alerting best practices',
      'Collaborate with product on technical feasibility'
    ],
    requirements: [
      '7+ years of backend development experience',
      'Strong experience with Python or Go',
      'Deep knowledge of PostgreSQL and Redis',
      'Experience with Kubernetes and cloud platforms',
      'Track record of building high-availability systems'
    ],
    niceToHave: [
      'Experience with event-driven architectures',
      'Background in HR/recruiting technology',
      'Previous startup experience'
    ],
    salaryRange: { min: 190000, max: 250000, currency: 'USD' },
    createdAt: '2024-01-08T00:00:00Z',
    updatedAt: '2024-01-10T00:00:00Z',
    closedAt: null
  },
  {
    id: 'pos-003',
    status: PositionStatus.OPEN,
    title: 'Product Designer',
    department: 'Design',
    location: 'New York, NY (Hybrid)',
    type: 'full-time',
    summary: 'Shape the future of HR software through thoughtful, user-centered design. You will own end-to-end design for key product areas, from research to high-fidelity prototypes.',
    responsibilities: [
      'Conduct user research and usability testing',
      'Create wireframes, prototypes, and high-fidelity designs',
      'Maintain and evolve our design system',
      'Partner closely with engineering on implementation',
      'Present design decisions to stakeholders'
    ],
    requirements: [
      '4+ years of product design experience',
      'Strong portfolio demonstrating UX process',
      'Expert-level Figma skills',
      'Experience with design systems',
      'Ability to translate complex workflows into simple UIs'
    ],
    niceToHave: [
      'Frontend development skills (HTML/CSS/JS)',
      'Experience with B2B SaaS products',
      'Motion design capabilities'
    ],
    salaryRange: { min: 130000, max: 175000, currency: 'USD' },
    createdAt: '2024-01-12T00:00:00Z',
    updatedAt: '2024-01-12T00:00:00Z',
    closedAt: null
  }
];

/**
 * Data access functions
 */

export function getAllPositions() {
  return positions;
}

export function getOpenPositions() {
  return positions.filter(p => p.status === PositionStatus.OPEN);
}

export function getPositionById(id) {
  return positions.find(p => p.id === id) || null;
}

export function searchPositions(query, filters = {}) {
  let results = [...positions];
  
  if (query) {
    const q = query.toLowerCase();
    results = results.filter(p =>
      p.title.toLowerCase().includes(q) ||
      p.department.toLowerCase().includes(q)
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
