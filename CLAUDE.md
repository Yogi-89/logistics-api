# CLAUDE.md — Logistics API

## Build & Run Commands
- **Run Development Server**: `uvicorn app.main:app --reload`
- **Database Migrations**:
  - Create migration: `alembic revision --autogenerate -m "description"`
  - Apply migrations: `alembic upgrade head`
- **Dependencies**: `pip install -r requirements.txt`

## Test & Lint Commands
- **Run All Tests**: `pytest`
- **Run Specific Test**: `pytest tests/test_filename.py`
- **Linting**: `flake8 .`

## Project Structure Notes
- `app/`: Core FastAPI application
  - `models/`: SQLAlchemy database models
  - `routers/`: API route handlers
  - `schemas/`: Pydantic models for validation
  - `utils/`: Helper functions
- `alembic/`: Database migration scripts
- `tests/`: Unit and integration tests
- `.env`: Environment variables (Copy from `.env.example` if available)
