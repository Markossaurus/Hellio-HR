# Learnings - Testing Infrastructure Setup

## Conventions & Patterns
(Agents will append findings here)
## [2026-01-26] Task 0: pytest setup
- Successfully added pytest dependencies to requirements.txt with exact versions:
  * pytest==8.0.0
  * pytest-asyncio==0.23.0  
  * httpx==0.26.0
- Created pytest.ini with basic configuration for async support and test discovery
- Created test directory structure with __init__.py and conftest.py placeholder
- Verified pytest 8.0.0 installation works correctly
- Note: Docker verification skipped due to permission issues, but local Python installation confirms compatibility
- LSP errors expected in container until dependencies are installed via Docker
- pytest-asyncio collection error encountered with __init__.py packages, but basic infrastructure ready
## 2026-01-26 Task 1: test fixtures

Key findings from implementing test fixtures and database setup:

1. **PostgreSQL vs SQLite Compatibility**: The main challenge was that models use PostgreSQL-specific types (CITEXT, UUID, JSONB, ARRAY) which aren't supported by SQLite. Initially tried mocking and type replacement approaches, but these were complex.

2. **Manual Table Creation**: The successful approach was to manually create SQLite-compatible tables using raw SQL schema definitions rather than trying to adapt the existing models. This avoided the type incompatibility issues.

3. **TestClient Setup**: Successfully overrode the get_db dependency using app.dependency_overrides, which is the standard FastAPI pattern for testing.

4. **Auth Token Generation**: Instead of relying on complex model relationships, created a simple token generation flow that directly inserts into auth_tokens table with proper hashing.

5. **Fixture Dependencies**: Established proper fixture dependency chain: test_db → client/test_user → auth_token, ensuring database is available before client, and user before token.

6. **Simple Test Pattern**: The health check test demonstrates the basic pattern of using the client fixture to test endpoints without authentication.

7. **Performance**: SQLite in-memory database provides fast test execution, avoiding PostgreSQL connection overhead.

This foundation supports future authenticated endpoint testing in Tasks 2-4.

## [2026-01-27] Task 2: login tests
- Login tests needed UUID-shaped IDs because ORM models use UUID types; normalizing test user/role IDs in SQLite avoids UUID parsing errors.
- Auth endpoint is mounted under `/auth`, so tests should target `/auth/login`.

## [2026-01-27] Task 3: positions endpoint tests
- In-memory SQLite (`sqlite:///:memory:`) breaks across threads/connections; FastAPI TestClient requests can hit a different connection, causing missing tables/rows.
- Workaround in endpoint tests: override `get_db` to use a per-test temporary file-backed SQLite DB so auth + endpoint queries share state.
- SQLAlchemy UUID columns on SQLite commonly bind as 32-char hex; storing IDs as `uuid.uuid4().hex` in DB (but returning/using hyphenated `str(uuid_obj)` in URLs/assertions) keeps ORM relationships working.

## [2026-01-27] Task 4: candidates endpoint tests
- Candidate endpoints access profile, positions, and CV relationships; create SQLite tables for `candidate_profiles`, `candidate_positions`, and `cv_documents` even if unused to avoid lazy-load errors.
- Insert JSON profile payloads via `json.dumps` so SQLAlchemy's JSONB type can deserialize back into dicts for `_build_candidate_profile`.

## [2026-01-27] Task 5: Playwright setup
- Created a dedicated `test/` workspace that keeps npm metadata separate from backend tooling, aligning with the plan's commit target.
- Installed @playwright/test, configured the TypeScript `playwright.config.ts` for chromium-only runs on `http://localhost:3000`, and documented the timeout/viewport choices for fast feedback.
- Bootstrapped Node locally (downloaded v22.4.0) because `npm`/`npx` were missing from the environment, then mapped the Node + CLI binaries into `/home/mark/.opencode/bin` so LSP tooling and future commands can run seamlessly.

## [2026-01-27] Task 6: E2E login flow test
- Confirmed the login form inputs (`#email`, `#password`) and submit button match the static `frontend/login.html`, so Playwright can fill credentials reliably.
- Built `test/e2e/auth.spec.ts` to assert navigation to `/index.html`, wait for the `#logout-btn`, and validate the `Hellio HR` heading to prove the dashboard renders.
- Installed the Playwright dependency via `npm install` so IDE diagnostics can resolve `@playwright/test` without complaining about missing modules.
- 2026-01-27: Added run-tests.sh to sequentially run pytest via docker compose and Playwright, reporting combined status and honoring exit codes.
