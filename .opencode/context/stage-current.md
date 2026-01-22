# Stage: Backend & Persistence (Stage 2)

## Context

In Exercise 1, the Hellio HR system established a **clear user-facing contract**:

* A normalized candidate profile JSON schema
* A frontend UI that depends on this schema to render candidates, positions, and comparisons

All data in Stage 1 was hardcoded and ephemeral.

This stage introduces a **real backend service and relational persistence layer**, while **preserving the UI contract** established earlier.

The primary challenge is **adding durability and structure without changing frontend behavior**.

---

## Core Principles

* **Preserve the UI contract** from Stage 1
* **Model the HR domain, not infrastructure**
* **Explicit structure over implicit behavior**
* **No automation magic** – everything is deterministic and explainable
* **Design for future ingestion and intelligence without implementing it yet**

---

## Goal

Design and implement a **FastAPI-based backend** backed by **PostgreSQL**, such that:

* Candidate, position, and CV data are persisted in a relational database
* The existing frontend loads all data from backend APIs
* Position details can be updated and persisted
* The system runs fully locally using containers

This stage results in a **fully demo-able end-to-end system**.

---

## In Scope

### Backend

* FastAPI backend service
* REST APIs for candidates and positions
* Role-based access control (read-only vs update)
* Streaming or serving CV documents via backend

### Database

* PostgreSQL database
* Explicit relational schema for:

  * users & roles
  * candidates
  * positions
  * candidate-position relationships
  * normalized candidate profiles (JSON)
  * CV document references

### Data Loading

* Manual loading of:

  * several candidates
  * several positions
  * several CV documents
* Data may be inserted using SQL scripts or manual tooling

### Infrastructure

* Local container-based setup

  * DB container (PostgreSQL)
  * Backend container (FastAPI)
  * Frontend container (already exists)

---

## Out of Scope

* Automatic CV parsing or extraction
* Semantic analysis or LLM usage
* Agents, MCP, or intelligent automation
* Performance optimizations
* UI changes beyond wiring to backend APIs
* File ingestion pipelines or loaders

---

## Stack

* **Backend:** FastAPI (Python)
* **Database:** PostgreSQL
* **Frontend:** Existing UI from Exercise 1 (unchanged)
* **Migrations:** Manual SQL migrations using a lightweight runner

---

## Database Design

The database models **domain concepts only**, not storage or ingestion mechanics.

### Entities

#### Users & Roles

* Users authenticate into the system
* Roles determine read-only vs update permissions

Tables:

* `users`
* `roles`
* `user_roles`

#### Candidates

* Represents a person being evaluated
* Contains identity and lifecycle status only

Table:

* `candidates`

#### Candidate Profiles

* Stores the **normalized candidate profile JSON** defined in Exercise 1
* One profile per candidate (no versioning yet)

Table:

* `candidate_profiles`

  * `profile_json` (JSONB)
  * `schema_version`

> This table preserves the frontend data contract.

#### Positions

* Represents an open or closed role
* Position details can be updated via the UI

Table:

* `positions`

#### Candidate–Position Relationship

* Explicit many-to-many mapping
* Represents which candidates are considered for which positions

Table:

* `candidate_positions`

#### CV Documents

* Represents the existence of a CV
* The database does **not** manage storage
* Documents are referenced via an opaque identifier

Table:

* `cv_documents`

  * `display_name`
  * `source` (e.g. `local`)
  * `reference` (opaque string resolved by backend)

---

## Database Migrations

Schema changes are managed using **manual SQL migrations**.

### Migration Tooling

Use a free, lightweight migration runner such as:

* **golang-migrate** (recommended)

Migrations are written as plain SQL files:

```
migrations/
  001_init_schema.sql
  002_seed_roles.sql
  003_seed_sample_data.sql
```

Migrations are applied explicitly and intentionally.

---

## Backend Responsibilities

The backend service must:

* Authenticate users
* Enforce role-based permissions
* Expose REST APIs matching frontend data needs
* Serve CV documents via HTTP
* Translate database rows into the existing UI JSON shape

### Required Endpoints (Minimum)

* `POST /auth/login`
* `GET /candidates`
* `GET /candidates/{id}`
* `GET /positions`
* `GET /positions/{id}`
* `PATCH /positions/{id}` (editor/admin only)
* `GET /cv-documents/{id}/download`

---

## Frontend Integration

* The frontend must load all data from backend APIs
* No frontend logic changes beyond replacing mock data with API calls
* UI behavior and layout must remain unchanged

---

## Local Development Setup

The system must run locally using containers:

* PostgreSQL container
* FastAPI backend container
* Frontend container

All services communicate via a local Docker network.

---

## Development Approach

Participants should:

1. Design and finalize the database schema
2. Write migrations before writing backend logic
3. Bring up DB and verify schema
4. Implement backend endpoints incrementally
5. Connect frontend and validate UI behavior
6. Commit after each vertical slice

---

## Validation & Self-Check

You should be able to answer **yes** to all of the following:

* Can I explain every table and why it exists?
* Does the frontend work without modification?
* Is all candidate data coming from the database?
* Can I update a position and see it persist?
* Can I locate where a CV is referenced and how it is served?
* If a new CV arrives tomorrow, do I know exactly where it fits?
* Can this system be demoed end-to-end locally?

---

## Done When

This stage is complete when:

* The backend service is running locally
* PostgreSQL contains candidate, position, and CV data
* The frontend loads all data from backend APIs
* Position updates persist correctly
* CVs are accessible via the UI
* The system can be demoed end-to-end without explanation
