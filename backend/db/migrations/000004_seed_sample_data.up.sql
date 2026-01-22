INSERT INTO positions (
  id,
  status,
  title,
  department,
  location,
  type,
  summary,
  responsibilities,
  requirements,
  nice_to_have,
  salary_min,
  salary_max,
  salary_currency,
  created_at,
  updated_at,
  closed_at
) VALUES
  (
    '11111111-1111-1111-1111-111111111111',
    'open',
    'Senior Frontend Engineer',
    'Engineering',
    'San Francisco, CA (Hybrid)',
    'full-time',
    'Join our product team to build the next generation of HR tools. You will lead frontend architecture decisions and mentor junior developers while shipping features that impact millions of users.',
    ARRAY[
      'Architect and implement complex React applications',
      'Collaborate with designers to deliver pixel-perfect UIs',
      'Mentor team members through code reviews and pairing',
      'Drive technical decisions and best practices',
      'Optimize application performance and accessibility'
    ],
    ARRAY[
      '5+ years of frontend development experience',
      'Expert-level TypeScript and React skills',
      'Experience with state management (Redux, Zustand, etc.)',
      'Strong understanding of web performance optimization',
      'Excellent communication skills'
    ],
    ARRAY[
      'Experience building design systems',
      'Familiarity with Node.js or Python backends',
      'Contributions to open source projects'
    ],
    160000,
    210000,
    'USD',
    '2024-01-05T00:00:00Z',
    '2024-01-05T00:00:00Z',
    NULL
  ),
  (
    '22222222-2222-2222-2222-222222222222',
    'open',
    'Staff Backend Engineer',
    'Engineering',
    'Remote (US)',
    'full-time',
    'We are scaling our platform to handle 10x growth. Looking for a seasoned backend engineer to design distributed systems, optimize database performance, and establish engineering standards.',
    ARRAY[
      'Design and build scalable microservices',
      'Own critical infrastructure components',
      'Lead technical design reviews',
      'Establish monitoring and alerting best practices',
      'Collaborate with product on technical feasibility'
    ],
    ARRAY[
      '7+ years of backend development experience',
      'Strong experience with Python or Go',
      'Deep knowledge of PostgreSQL and Redis',
      'Experience with Kubernetes and cloud platforms',
      'Track record of building high-availability systems'
    ],
    ARRAY[
      'Experience with event-driven architectures',
      'Background in HR/recruiting technology',
      'Previous startup experience'
    ],
    190000,
    250000,
    'USD',
    '2024-01-08T00:00:00Z',
    '2024-01-10T00:00:00Z',
    NULL
  ),
  (
    '33333333-3333-3333-3333-333333333333',
    'open',
    'Product Designer',
    'Design',
    'New York, NY (Hybrid)',
    'full-time',
    'Shape the future of HR software through thoughtful, user-centered design. You will own end-to-end design for key product areas, from research to high-fidelity prototypes.',
    ARRAY[
      'Conduct user research and usability testing',
      'Create wireframes, prototypes, and high-fidelity designs',
      'Maintain and evolve our design system',
      'Partner closely with engineering on implementation',
      'Present design decisions to stakeholders'
    ],
    ARRAY[
      '4+ years of product design experience',
      'Strong portfolio demonstrating UX process',
      'Expert-level Figma skills',
      'Experience with design systems',
      'Ability to translate complex workflows into simple UIs'
    ],
    ARRAY[
      'Frontend development skills (HTML/CSS/JS)',
      'Experience with B2B SaaS products',
      'Motion design capabilities'
    ],
    130000,
    175000,
    'USD',
    '2024-01-12T00:00:00Z',
    '2024-01-12T00:00:00Z',
    NULL
  );

INSERT INTO candidates (
  id,
  status,
  name,
  email,
  phone,
  location,
  title,
  created_at,
  updated_at
) VALUES
  (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'active',
    'Sarah Chen',
    'sarah.chen@email.com',
    '+1-415-555-0142',
    'San Francisco, CA',
    'Senior Full-Stack Engineer',
    '2024-01-10T09:30:00Z',
    '2024-01-15T14:20:00Z'
  ),
  (
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'active',
    'Marcus Johnson',
    'marcus.j@email.com',
    '+1-512-555-0198',
    'Austin, TX (Remote)',
    'Backend Engineer',
    '2024-01-12T11:00:00Z',
    '2024-01-12T11:00:00Z'
  ),
  (
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'active',
    'Elena Rodriguez',
    'elena.r@email.com',
    '+1-646-555-0167',
    'New York, NY',
    'Product Designer & Frontend Developer',
    '2024-01-14T16:45:00Z',
    '2024-01-14T16:45:00Z'
  );

INSERT INTO candidate_profiles (
  id,
  candidate_id,
  profile_json,
  created_at,
  updated_at
) VALUES
  (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    $$
    {
      "id": "cand-001",
      "status": "active",
      "name": "Sarah Chen",
      "email": "sarah.chen@email.com",
      "phone": "+1-415-555-0142",
      "location": "San Francisco, CA",
      "title": "Senior Full-Stack Engineer",
      "summary": "Results-driven engineer with 7+ years building scalable web applications. Led teams of 5-8 developers. Strong focus on performance optimization and clean architecture.",
      "skills": [
        {"id": "sk-001", "name": "TypeScript", "level": "expert"},
        {"id": "sk-002", "name": "React", "level": "expert"},
        {"id": "sk-003", "name": "Node.js", "level": "advanced"},
        {"id": "sk-004", "name": "PostgreSQL", "level": "advanced"},
        {"id": "sk-005", "name": "AWS", "level": "intermediate"},
        {"id": "sk-006", "name": "GraphQL", "level": "advanced"}
      ],
      "experience": [
        {
          "id": "exp-001",
          "company": "Stripe",
          "title": "Senior Software Engineer",
          "startDate": "2021-03",
          "endDate": "present",
          "description": "Lead frontend architect for payment dashboard. Reduced page load time by 40%."
        },
        {
          "id": "exp-002",
          "company": "Airbnb",
          "title": "Software Engineer",
          "startDate": "2018-06",
          "endDate": "2021-02",
          "description": "Built search infrastructure components. Mentored 3 junior engineers."
        },
        {
          "id": "exp-003",
          "company": "Startup Labs",
          "title": "Junior Developer",
          "startDate": "2016-08",
          "endDate": "2018-05",
          "description": "Full-stack development for e-commerce platform."
        }
      ],
      "education": [
        {
          "id": "edu-001",
          "institution": "UC Berkeley",
          "degree": "B.S.",
          "field": "Computer Science",
          "startDate": "2012-09",
          "endDate": "2016-05"
        }
      ],
      "positionIds": ["pos-001", "pos-002"],
      "cvDocument": {
        "filename": "sarah-chen-cv.pdf",
        "path": "assets/cvs/sarah-chen-cv.pdf",
        "uploadedAt": "2024-01-10T09:30:00Z"
      },
      "createdAt": "2024-01-10T09:30:00Z",
      "updatedAt": "2024-01-15T14:20:00Z"
    }
    $$::jsonb,
    '2024-01-10T09:30:00Z',
    '2024-01-15T14:20:00Z'
  ),
  (
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb2',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    $$
    {
      "id": "cand-002",
      "status": "active",
      "name": "Marcus Johnson",
      "email": "marcus.j@email.com",
      "phone": "+1-512-555-0198",
      "location": "Austin, TX (Remote)",
      "title": "Backend Engineer",
      "summary": "Passionate about distributed systems and API design. 5 years of experience in high-traffic environments. Open source contributor.",
      "skills": [
        {"id": "sk-010", "name": "Python", "level": "expert"},
        {"id": "sk-011", "name": "Go", "level": "advanced"},
        {"id": "sk-012", "name": "Kubernetes", "level": "advanced"},
        {"id": "sk-013", "name": "PostgreSQL", "level": "expert"},
        {"id": "sk-014", "name": "Redis", "level": "advanced"},
        {"id": "sk-015", "name": "gRPC", "level": "intermediate"}
      ],
      "experience": [
        {
          "id": "exp-010",
          "company": "Datadog",
          "title": "Backend Engineer",
          "startDate": "2022-01",
          "endDate": "present",
          "description": "Building metrics ingestion pipeline handling 2M events/sec."
        }
      ],
      "education": [
        {
          "id": "edu-010",
          "institution": "University of Texas",
          "degree": "M.S.",
          "field": "Computer Science",
          "startDate": "2017-09",
          "endDate": "2019-05"
        },
        {
          "id": "edu-011",
          "institution": "Texas A&M",
          "degree": "B.S.",
          "field": "Software Engineering",
          "startDate": "2013-09",
          "endDate": "2017-05"
        }
      ],
      "positionIds": ["pos-002"],
      "cvDocument": {
        "filename": "marcus-johnson-cv.pdf",
        "path": "assets/cvs/marcus-johnson-cv.pdf",
        "uploadedAt": "2024-01-12T11:00:00Z"
      },
      "createdAt": "2024-01-12T11:00:00Z",
      "updatedAt": "2024-01-12T11:00:00Z"
    }
    $$::jsonb,
    '2024-01-12T11:00:00Z',
    '2024-01-12T11:00:00Z'
  ),
  (
    'cccccccc-cccc-cccc-cccc-ccccccccccc3',
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    $$
    {
      "id": "cand-003",
      "status": "active",
      "name": "Elena Rodriguez",
      "email": "elena.r@email.com",
      "phone": "+1-646-555-0167",
      "location": "New York, NY",
      "title": "Product Designer & Frontend Developer",
      "summary": "Hybrid designer-developer with 6 years crafting user experiences. Figma expert. Strong in design systems, accessibility, and React implementation.",
      "skills": [
        {"id": "sk-020", "name": "Figma", "level": "expert"},
        {"id": "sk-021", "name": "React", "level": "advanced"},
        {"id": "sk-022", "name": "CSS/Tailwind", "level": "expert"},
        {"id": "sk-023", "name": "TypeScript", "level": "intermediate"},
        {"id": "sk-024", "name": "User Research", "level": "advanced"},
        {"id": "sk-025", "name": "Accessibility", "level": "advanced"}
      ],
      "experience": [
        {
          "id": "exp-020",
          "company": "Figma",
          "title": "Product Designer",
          "startDate": "2022-06",
          "endDate": "present",
          "description": "Design systems team. Shipped component library used by 200+ designers."
        },
        {
          "id": "exp-021",
          "company": "Shopify",
          "title": "UX Engineer",
          "startDate": "2019-03",
          "endDate": "2022-05",
          "description": "Bridged design and engineering. Built Polaris components."
        },
        {
          "id": "exp-022",
          "company": "Agency Co",
          "title": "UI Designer",
          "startDate": "2017-06",
          "endDate": "2019-02",
          "description": "Client-facing design work for Fortune 500 companies."
        }
      ],
      "education": [
        {
          "id": "edu-020",
          "institution": "Parsons School of Design",
          "degree": "B.F.A.",
          "field": "Design & Technology",
          "startDate": "2013-09",
          "endDate": "2017-05"
        }
      ],
      "positionIds": ["pos-001"],
      "cvDocument": {
        "filename": "elena-rodriguez-cv.pdf",
        "path": "assets/cvs/elena-rodriguez-cv.pdf",
        "uploadedAt": "2024-01-14T16:45:00Z"
      },
      "createdAt": "2024-01-14T16:45:00Z",
      "updatedAt": "2024-01-14T16:45:00Z"
    }
    $$::jsonb,
    '2024-01-14T16:45:00Z',
    '2024-01-14T16:45:00Z'
  );

INSERT INTO cv_documents (
  id,
  candidate_id,
  display_name,
  source,
  reference,
  uploaded_at
) VALUES
  (
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'sarah-chen-cv.pdf',
    'local',
    'cvs/sarah-chen-cv.pdf',
    '2024-01-10T09:30:00Z'
  ),
  (
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'marcus-johnson-cv.pdf',
    'local',
    'cvs/marcus-johnson-cv.pdf',
    '2024-01-12T11:00:00Z'
  ),
  (
    'ffffffff-ffff-ffff-ffff-ffffffffffff',
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'elena-rodriguez-cv.pdf',
    'local',
    'cvs/elena-rodriguez-cv.pdf',
    '2024-01-14T16:45:00Z'
  );

INSERT INTO candidate_positions (
  id,
  candidate_id,
  position_id,
  stage,
  applied_at,
  created_at,
  updated_at
) VALUES
  (
    '10000000-0000-0000-0000-000000000001',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    '11111111-1111-1111-1111-111111111111',
    'applied',
    '2024-01-10T09:30:00Z',
    '2024-01-10T09:30:00Z',
    '2024-01-15T14:20:00Z'
  ),
  (
    '10000000-0000-0000-0000-000000000002',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    '22222222-2222-2222-2222-222222222222',
    'applied',
    '2024-01-10T09:30:00Z',
    '2024-01-10T09:30:00Z',
    '2024-01-15T14:20:00Z'
  ),
  (
    '10000000-0000-0000-0000-000000000003',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    '22222222-2222-2222-2222-222222222222',
    'applied',
    '2024-01-12T11:00:00Z',
    '2024-01-12T11:00:00Z',
    '2024-01-12T11:00:00Z'
  ),
  (
    '10000000-0000-0000-0000-000000000004',
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    '11111111-1111-1111-1111-111111111111',
    'applied',
    '2024-01-14T16:45:00Z',
    '2024-01-14T16:45:00Z',
    '2024-01-14T16:45:00Z'
  );
