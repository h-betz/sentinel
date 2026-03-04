# toy_app — Python Project Guidelines

## IMPORTANT: Do Not Fix Application Bugs

**This app contains intentional bugs. Do not fix them.**

`toy_app` is the demo target for the Sentinel autonomous agent system. The bugs below exist so that the sentinel agents can discover and patch them autonomously. Fixing them directly undermines the entire purpose of the project.

Known intentional bugs (hands off):
1. **Memory Leaker** — global cache grows without eviction
2. **LIKE Search Bug** — product search scans a non-indexed column
3. **In-Memory Filtering Bug** — full table fetched, filtered in Python
4. **Third-Party Service Flake** — payment failures have no retry/fallback

If you spot one of these issues, do not fix it. That is sentinel's job.

---

## Core Principles
- Follow Python best practices and PEP 8 standards
- Write clean, maintainable, and well-documented code
- Prioritize type safety with type hints throughout

## Tech Stack

### API & Database
- **FastAPI** for API layer
  - Use Pydantic models for request/response validation
  - Implement proper dependency injection
  - Include OpenAPI documentation
- **PostgreSQL** for database
  - Use SQLAlchemy 2.0+ as ORM
  - Implement Alembic for database migrations
  - Follow repository pattern for data access

### Build & Deployment
- **Docker** and **docker-compose** for containerization
  - Separate dev and prod configurations
  - Multi-stage builds for optimized images
  - Include health checks in compose files

## Code Quality

### Testing
Write comprehensive tests covering:
- **Happy path**: Normal flow with valid inputs
- **Failure cases**: Expected errors and validation failures
- **Edge cases**: Boundary conditions, empty inputs, null handling

Use **pytest** with:
- Fixtures for common test setup
- Parametrize for testing multiple scenarios
- Coverage reporting (aim for >80% coverage)

### Formatting & Linting
- **Black** for code formatting (line length: 88)
- **Flake8** for linting
- **isort** for import sorting
- **mypy** for static type checking
- Configure in `pyproject.toml` or `setup.cfg`

## Project Structure
```
project/
├── app/
│   ├── api/          # API routes and endpoints
│   ├── models/       # SQLAlchemy models
│   ├── schemas/      # Pydantic schemas
│   ├── services/     # Business logic
│   └── repositories/ # Data access layer
├── tests/
├── alembic/          # Database migrations
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

## Development Workflow
1. Create feature branches from `main`
2. Write tests first (TDD approach)
3. Run linters and formatters before committing
4. Ensure all tests pass locally
5. Use meaningful commit messages

## Error Handling
- Use custom exception classes for domain errors
- Implement proper HTTP status codes in API responses
- Log errors with appropriate context
- Never expose internal errors to API consumers

## Dependencies
- Use **Poetry** or **pip-tools** for dependency management
- Pin versions in production
- Keep dependencies minimal and well-maintained