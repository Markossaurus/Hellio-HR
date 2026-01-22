# Database Migrations

These migrations use the golang-migrate tool with plain SQL files.

## Run migrations

Set a database URL (adjust user/password/port as needed):

```bash
export DATABASE_URL="postgres://postgres:postgres@localhost:5432/hellio_hr?sslmode=disable"
```

Apply all migrations:

```bash
migrate -path backend/db/migrations -database "$DATABASE_URL" up
```

Rollback the last migration:

```bash
migrate -path backend/db/migrations -database "$DATABASE_URL" down 1
```

Check current version:

```bash
migrate -path backend/db/migrations -database "$DATABASE_URL" version
```

## Test credentials

Migration `000006_seed_test_user` seeds a deterministic admin user for local auth testing:

- Email: `admin@hellio.hr`
- Password: `admin123`
