CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email CITEXT UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE roles (
  id UUID PRIMARY KEY,
  name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE user_roles (
  user_id UUID REFERENCES users(id),
  role_id UUID REFERENCES roles(id),
  PRIMARY KEY (user_id, role_id)
);

CREATE TABLE candidates (
  id UUID PRIMARY KEY,
  status VARCHAR(20) NOT NULL,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255),
  phone VARCHAR(50),
  location VARCHAR(255),
  title VARCHAR(255),
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
);

CREATE TABLE candidate_profiles (
  id UUID PRIMARY KEY,
  candidate_id UUID UNIQUE REFERENCES candidates(id),
  profile_json JSONB NOT NULL,
  schema_version VARCHAR(20) DEFAULT '1.0',
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
);

CREATE TABLE positions (
  id UUID PRIMARY KEY,
  status VARCHAR(20) NOT NULL,
  title VARCHAR(255) NOT NULL,
  department VARCHAR(100),
  location VARCHAR(255),
  type VARCHAR(50),
  summary TEXT,
  responsibilities TEXT[],
  requirements TEXT[],
  nice_to_have TEXT[],
  salary_min INTEGER,
  salary_max INTEGER,
  salary_currency VARCHAR(10) DEFAULT 'USD',
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ,
  closed_at TIMESTAMPTZ
);

CREATE TABLE candidate_positions (
  id UUID PRIMARY KEY,
  candidate_id UUID REFERENCES candidates(id),
  position_id UUID REFERENCES positions(id),
  stage VARCHAR(50) DEFAULT 'applied',
  applied_at TIMESTAMPTZ DEFAULT now(),
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ,
  UNIQUE (candidate_id, position_id)
);

CREATE TABLE cv_documents (
  id UUID PRIMARY KEY,
  candidate_id UUID REFERENCES candidates(id),
  display_name VARCHAR(255) NOT NULL,
  source VARCHAR(50) DEFAULT 'local',
  reference VARCHAR(500) NOT NULL,
  uploaded_at TIMESTAMPTZ
);
