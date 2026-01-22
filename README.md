## Getting Started (Docker)

### Prerequisites
- Docker and Docker Compose

### Start the application

1. Start the database:
   ```bash
   docker compose up -d db
   ```

2. Run migrations:
   ```bash
   docker compose run --rm migrate
   ```

3. Start all services:
   ```bash
   docker compose up
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Login: admin@hellio.hr / admin123

### Development

- Backend code changes auto-reload (uvicorn --reload)
- Frontend changes are immediate (volume mounted)
- Database data persists in Docker volume

### Useful commands

```bash
# View logs
docker compose logs -f backend

# Rebuild after dependency changes
docker compose build backend

# Reset database
docker compose down -v
docker compose up -d db
docker compose run --rm migrate

# Run migrations
docker compose run --rm migrate up

# Rollback last migration
docker compose run --rm migrate down 1
```
