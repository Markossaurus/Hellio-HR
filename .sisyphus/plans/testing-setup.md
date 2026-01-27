# Testing Infrastructure Setup for Hellio-HR

## Context

### Original Request
Set up E2E testing infrastructure so AI sub-agents can verify their code changes through a self-verification loop. Tests serve as quality gates for AI-generated code.

### Interview Summary
**Key Discussions**:
- **Purpose**: Regression prevention, safe refactoring, sub-agent self-verification
- **Surfaces**: API endpoints, Database operations, Web UI flows
- **Organization**: By feature (`test/auth/`, `test/positions/`, etc.)
- **Speed**: Fast feedback (<60s) for quick agent verification loops
- **Workflow**: Agents run tests after changes, use results to self-correct

**Tech Stack**:
- Backend: Python FastAPI + SQLAlchemy + PostgreSQL
- Frontend: Vanilla HTML/CSS/JS (nginx)
- Infrastructure: Docker Compose
- Existing tests: None

### Self-Review (Metis unavailable)
**Gaps Identified**:
1. Test database strategy needed (in-memory vs container)
2. CI integration not discussed (out of scope for now)
3. Coverage thresholds not set (defer to organic growth)

**Defaults Applied**:
- pytest for backend (industry standard for FastAPI)
- Playwright for E2E (supports API + browser testing)
- SQLite in-memory for fast test DB (no container spin-up)

---

## Work Objectives

### Core Objective
Set up a complete testing infrastructure that enables AI sub-agents to verify their code changes through fast, reliable automated tests.

### Concrete Deliverables
- `test/` directory with feature-organized structure
- pytest configuration for backend API/DB testing
- Playwright configuration for E2E browser testing
- Test fixtures for database seeding
- Example tests for each feature area
- Single command to run all tests

### Definition of Done
- [x] `pytest` runs backend tests successfully
- [x] `playwright test` runs E2E tests successfully
- [x] Full test suite completes in <60 seconds
- [x] Tests are organized by feature

### Must Have
- pytest + pytest-asyncio for FastAPI testing
- Playwright for browser automation
- In-memory SQLite for fast test database
- Test fixtures for auth (login, token generation)
- At least one test per feature area (auth, positions, candidates)

### Must NOT Have (Guardrails)
- NO complex test infrastructure (keep it simple)
- NO coverage enforcement (organic growth)
- NO CI/CD setup (separate concern)
- NO mocking of database (use real test DB)
- NO parallel browser tests (keep simple for now)

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: NO (setting up from scratch)
- **User wants tests**: YES (E2E for agent verification)
- **Framework**: pytest (backend) + Playwright (E2E)

### Test Execution Commands
```bash
# Backend tests only (fast)
docker compose run --rm backend pytest test/ -v

# E2E tests only (requires running app)
npx playwright test

# All tests
./run-tests.sh
```

---

## Task Flow

```
Task 0 (pytest setup) → Task 1 (fixtures) → Task 2 (auth tests)
                                         → Task 3 (positions tests)
                                         → Task 4 (candidates tests)
                     → Task 5 (Playwright setup) → Task 6 (E2E tests)
Task 7 (test script) depends on all above
```

## Parallelization

| Group | Tasks | Reason |
|-------|-------|--------|
| A | 2, 3, 4 | Independent feature tests after fixtures |
| B | 5, 6 | Playwright setup is independent of pytest |

| Task | Depends On | Reason |
|------|------------|--------|
| 1 | 0 | Fixtures need pytest installed |
| 2, 3, 4 | 1 | Tests need fixtures |
| 6 | 5 | E2E tests need Playwright installed |
| 7 | All | Script combines all test commands |

---

## TODOs

- [x] 0. Set up pytest for backend testing

  **What to do**:
  - Add pytest dependencies to `backend/requirements.txt`:
    - `pytest==8.0.0`
    - `pytest-asyncio==0.23.0`
    - `httpx==0.26.0` (for TestClient)
  - Create `backend/pytest.ini` with configuration
  - Create `backend/test/` directory structure:
    - `backend/test/__init__.py`
    - `backend/test/conftest.py` (shared fixtures)

  **Must NOT do**:
  - Don't add coverage tools yet
  - Don't configure parallel execution

  **Parallelizable**: NO (foundational task)

  **References**:
  - `backend/requirements.txt` - Add test dependencies here
  - `backend/app/main.py` - FastAPI app to test against
  - `backend/app/db.py` - Database session pattern to override in tests
  - pytest docs: https://docs.pytest.org/en/stable/

  **Acceptance Criteria**:
  - [ ] `docker compose run --rm backend pip install -r requirements.txt` succeeds
  - [ ] `docker compose run --rm backend pytest --version` shows pytest 8.x
  - [ ] Directory structure exists: `backend/test/conftest.py`

  **Commit**: YES
  - Message: `test(backend): add pytest infrastructure`
  - Files: `backend/requirements.txt`, `backend/pytest.ini`, `backend/test/`

---

- [x] 1. Create test fixtures and database setup

  **What to do**:
  - In `backend/test/conftest.py`, create:
    - `test_db` fixture: SQLite in-memory database
    - `client` fixture: FastAPI TestClient with test DB
    - `auth_token` fixture: Valid JWT token for authenticated requests
    - `test_user` fixture: Create test user in DB
  - Override FastAPI's `get_db` dependency for tests

  **Must NOT do**:
  - Don't use PostgreSQL for tests (too slow)
  - Don't create complex factory patterns yet

  **Parallelizable**: NO (depends on Task 0)

  **References**:
  - `backend/app/db.py:get_db` - Dependency to override
  - `backend/app/auth.py:create_token` - Token creation for auth fixture
  - `backend/app/models.py` - SQLAlchemy models to create tables
  - `backend/app/main.py:app` - FastAPI app instance

  **Acceptance Criteria**:
  - [ ] Create minimal test in `backend/test/test_health.py`:
    ```python
    def test_health(client):
        response = client.get("/health")
        # If no health endpoint, test root or any endpoint
    ```
  - [ ] `docker compose run --rm backend pytest backend/test/ -v` shows fixtures work

  **Commit**: YES
  - Message: `test(backend): add test fixtures and database setup`
  - Files: `backend/test/conftest.py`, `backend/test/test_health.py`

---

- [x] 2. Add auth endpoint tests

  **What to do**:
  - Create `backend/test/auth/test_login.py`
  - Test cases:
    - Valid login returns token and user info
    - Invalid email returns 401
    - Invalid password returns 401
    - Missing fields return 422

  **Must NOT do**:
  - Don't test logout (endpoint doesn't exist)
  - Don't test registration (endpoint doesn't exist)

  **Parallelizable**: YES (with 3, 4)

  **References**:
  - `backend/app/routes/auth.py:login` - Endpoint under test
  - `backend/app/schemas.py:LoginRequest` - Request schema
  - `backend/app/schemas.py:LoginResponse` - Response schema
  - `backend/test/conftest.py:test_user` - Use this fixture

  **Acceptance Criteria**:
  - [ ] `docker compose run --rm backend pytest backend/test/auth/ -v`
  - [ ] At least 3 test cases pass
  - [ ] Tests complete in <5 seconds

  **Commit**: YES
  - Message: `test(auth): add login endpoint tests`
  - Files: `backend/test/auth/test_login.py`

---

- [x] 3. Add positions endpoint tests

  **What to do**:
  - Create `backend/test/positions/test_positions.py`
  - Test cases:
    - List positions (authenticated)
    - List positions (unauthenticated) returns 401
    - Get single position by ID
    - Get non-existent position returns 404
    - Filter positions by status

  **Must NOT do**:
  - Don't test create/delete (endpoints may not exist)
  - Don't test complex permission scenarios yet

  **Parallelizable**: YES (with 2, 4)

  **References**:
  - `backend/app/routes/positions.py` - All position endpoints
  - `backend/app/models.py:Position` - Position model for fixtures
  - `backend/app/schemas.py:PositionResponse` - Response shape

  **Acceptance Criteria**:
  - [ ] `docker compose run --rm backend pytest backend/test/positions/ -v`
  - [ ] At least 4 test cases pass
  - [ ] Tests complete in <5 seconds

  **Commit**: YES
  - Message: `test(positions): add position endpoint tests`
  - Files: `backend/test/positions/test_positions.py`

---

- [x] 4. Add candidates endpoint tests

  **What to do**:
  - Create `backend/test/candidates/test_candidates.py`
  - Test cases:
    - List candidates (authenticated)
    - List candidates (unauthenticated) returns 401
    - Get single candidate by ID
    - Get non-existent candidate returns 404
    - Filter candidates by status

  **Must NOT do**:
  - Don't test CV upload (complex, separate task)
  - Don't test candidate creation if endpoint doesn't exist

  **Parallelizable**: YES (with 2, 3)

  **References**:
  - `backend/app/routes/candidates.py` - All candidate endpoints
  - `backend/app/models.py:Candidate` - Candidate model
  - `backend/app/schemas.py:CandidateResponse` - Response shape

  **Acceptance Criteria**:
  - [ ] `docker compose run --rm backend pytest backend/test/candidates/ -v`
  - [ ] At least 4 test cases pass
  - [ ] Tests complete in <5 seconds

  **Commit**: YES
  - Message: `test(candidates): add candidate endpoint tests`
  - Files: `backend/test/candidates/test_candidates.py`

---

- [x] 5. Set up Playwright for E2E testing

  **What to do**:
  - Create `test/` directory at project root for E2E tests
  - Create `test/package.json` with Playwright dependency
  - Create `test/playwright.config.ts` with:
    - Base URL: `http://localhost:3000`
    - Single browser (chromium) for speed
    - Timeout settings for fast feedback
  - Install Playwright: `npm install && npx playwright install chromium`

  **Must NOT do**:
  - Don't configure multiple browsers (keep fast)
  - Don't set up video recording
  - Don't configure parallel workers

  **Parallelizable**: YES (independent of pytest tasks)

  **References**:
  - `frontend/index.html` - Main page to test
  - `frontend/login.html` - Login page
  - `docker-compose.yml` - Frontend runs on port 3000
  - Playwright docs: https://playwright.dev/docs/intro

  **Acceptance Criteria**:
  - [ ] `cd test && npm install` succeeds
  - [ ] `cd test && npx playwright --version` shows Playwright installed
  - [ ] `test/playwright.config.ts` exists with correct base URL

  **Commit**: YES
  - Message: `test(e2e): add Playwright infrastructure`
  - Files: `test/package.json`, `test/playwright.config.ts`

---

- [x] 6. Add E2E login flow test

  **What to do**:
  - Create `test/e2e/auth.spec.ts`
  - Test cases:
    - Navigate to login page
    - Fill credentials, submit form
    - Verify redirect to dashboard/main page
    - Verify user is logged in (check UI element)

  **Must NOT do**:
  - Don't test edge cases in E2E (leave to unit tests)
  - Don't test multiple browsers

  **Parallelizable**: NO (depends on Task 5)

  **References**:
  - `frontend/login.html` - Login form structure
  - `frontend/js/login-app.js` - Login form handling
  - `frontend/index.html` - Post-login destination
  - README: Default credentials `admin@hellio.hr / admin123`

  **Acceptance Criteria**:
  - [ ] Start app: `docker compose up -d`
  - [ ] Run test: `cd test && npx playwright test`
  - [ ] Test passes, shows login → dashboard flow works
  - [ ] Test completes in <10 seconds

  **Commit**: YES
  - Message: `test(e2e): add login flow test`
  - Files: `test/e2e/auth.spec.ts`

---

- [x] 7. Create unified test runner script

  **What to do**:
  - Create `run-tests.sh` at project root
  - Script should:
    1. Run backend pytest tests
    2. Run Playwright E2E tests (if app is running)
    3. Report combined results
  - Make script executable

  **Must NOT do**:
  - Don't auto-start docker compose (let user control)
  - Don't add complex reporting

  **Parallelizable**: NO (depends on all previous tasks)

  **References**:
  - All previous test configurations
  - `docker-compose.yml` - For running backend tests

  **Acceptance Criteria**:
  - [ ] `chmod +x run-tests.sh`
  - [ ] `./run-tests.sh` runs all tests
  - [ ] Script exits with 0 if all pass, non-zero if any fail
  - [ ] Total execution time <60 seconds

  **Commit**: YES
  - Message: `test: add unified test runner script`
  - Files: `run-tests.sh`

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 0 | `test(backend): add pytest infrastructure` | requirements.txt, pytest.ini | pytest --version |
| 1 | `test(backend): add test fixtures and database setup` | conftest.py | pytest -v |
| 2 | `test(auth): add login endpoint tests` | test_login.py | pytest auth/ |
| 3 | `test(positions): add position endpoint tests` | test_positions.py | pytest positions/ |
| 4 | `test(candidates): add candidate endpoint tests` | test_candidates.py | pytest candidates/ |
| 5 | `test(e2e): add Playwright infrastructure` | package.json, config | playwright --version |
| 6 | `test(e2e): add login flow test` | auth.spec.ts | playwright test |
| 7 | `test: add unified test runner script` | run-tests.sh | ./run-tests.sh |

---

## Success Criteria

### Verification Commands
```bash
# Backend tests
docker compose run --rm backend pytest backend/test/ -v
# Expected: All tests pass, <30s

# E2E tests (requires running app)
docker compose up -d
cd test && npx playwright test
# Expected: Login flow passes, <30s

# Full suite
./run-tests.sh
# Expected: Exit 0, <60s total
```

### Final Checklist
- [x] All "Must Have" present (pytest, playwright, fixtures, feature tests)
- [x] All "Must NOT Have" absent (no coverage, no CI, no complex infra)
- [x] All backend tests pass
- [x] All E2E tests pass
- [x] Total suite runs in <60 seconds
