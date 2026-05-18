# Agridesk Backend

FastAPI backend for Agridesk (Academic Letter Workflow System).

## Stack

- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Pydantic Settings
- Pytest

## Project Structure

```text
backend/
  app/
    controllers/    # HTTP routes (thin controllers)
    services/       # Business logic orchestration
    repositories/   # Data access (Domain <-> ORM mapping)
    models/         # SQLAlchemy ORM models (Anemic data containers)
    schemas/        # Request/response schemas
    domain/         # Rich Domain Models (State Machines, pure Python)
    utils/          # Security, uploads, PDF/QR/hash helpers
    main.py         # FastAPI app entrypoint & Global Exception Handler
    config.py       # Settings loader (.env)
    database.py     # DB engine/session/base
  alembic/          # DB migrations
  tests/            # Service-level tests (In-Memory SQLite)
  .env.example
  requirements.txt
```

## Architectural Principles

Agridesk backend strictly adheres to Clean Architecture and Domain-Driven Design (DDD):
- **Rich Domain Model & State Machine**: The `domain/` layer contains pure Python dataclasses (e.g., `Surat`). All business rules and status transitions (e.g., `DRAFT` -> `MENUNGGU_TTD_DOSEN`) are encapsulated within these models using strict Finite State Machines.
- **Data Access Abstraction**: The `repositories/` layer acts as a two-way mapper. It translates raw SQLAlchemy ORM rows (`models/`) into pure `domain/` objects for the service layer, ensuring the business logic never leaks database implementation details.
- **Exception Hierarchy**: All custom errors inherit from a base `AgrideskError`. A single global exception handler in `main.py` catches these and polymorphically returns structured HTTP JSON responses, maintaining the Open/Closed Principle.
- **Cryptographic Signatures**: The system uses SHA-256 to hash finalized PDF binaries. The hash is embedded into a generated QR code and permanently flattened onto the physical PDF, creating a tamper-proof verification chain.


## Prerequisites

- Python 3.11+
- PostgreSQL running locally (or update `DATABASE_URL`)

## Environment Variables

Copy `.env.example` to `.env` and update values.

```dotenv
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agridesk
SECRET_KEY=change-this-secret-key-in-production
DB_INIT_ON_STARTUP=true
DB_INIT_FAIL_FAST=false
```

Notes:
- `config.py` reads env vars from `backend/.env`.
- `SECRET_KEY` must be changed for non-local environments.

## Install Dependencies

From `backend/`:

```bash
pip install -r requirements.txt
```

If you use the workspace venv from repo root on Windows:

```powershell
c:/Users/faizn/ads-agridesk/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
```

## Database Migrations (Alembic)

From `backend/`:

```bash
alembic upgrade head
```

Create a new migration after model changes:

```bash
alembic revision --autogenerate -m "describe_change"
alembic upgrade head
```

## Run the API

From `backend/`:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Health/root:
- `GET /` -> `{"message": "Agridesk API is running"}`

## Auth and Roles

JWT bearer auth is used.

Roles:
- `MAHASISWA`
- `DOSEN`
- `ADMIN`

Use `POST /api/auth/login` to get `access_token`, then send:

```text
Authorization: Bearer <token>
```

## Core Endpoints

Authentication:
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

Surat:
- `POST /api/surat/internal`
- `POST /api/surat/external` (multipart + PDF upload)
- `POST /api/surat/{surat_id}/submit`
- `GET /api/surat/my`
- `GET /api/surat/pending` (admin)
- `POST /api/surat/{surat_id}/approve` (admin)
- `POST /api/surat/{surat_id}/reject` (admin/dosen)
- `GET /api/surat/all` (admin)
- `GET /api/surat/{surat_id}`

Signatures:
- `POST /api/signatures/student/{surat_id}`
- `POST /api/signatures/lecturer/{signature_id}/sign`
- `GET /api/signatures/pending`
- `GET /api/signatures/surat/{surat_id}`

Verification:
- `GET /verify/{document_hash}`

## File Upload Rules

Enforced in `app/utils/upload.py`:
- External letter upload: PDF only (`application/pdf`), max 10 MB
- Signature upload: PNG/JPG/JPEG, max 2 MB
- Filenames are generated safely with UUID-based naming

## Running Tests

From `backend/`:

```bash
pytest tests/ -v --tb=short
```

Windows (workspace venv):

```powershell
c:/Users/faizn/ads-agridesk/.venv/Scripts/python.exe -m pytest tests/ -v --tb=short
```

## Frontend Integration Notes

- CORS currently allows `http://localhost:5173`.
- Backend expects bearer token for protected routes.
- Use `/docs` as the source of truth for request/response shapes.
- Keep base URL configurable in frontend (for local/prod).

## Common Local Issues

`ModuleNotFoundError: No module named 'app'`
- Run from `backend/` and use: `python -m uvicorn app.main:app --reload`

`password authentication failed for user "postgres"`
- Check `DATABASE_URL` credentials in `backend/.env`
- Ensure PostgreSQL user/password/database exist and are correct

`An environment file is configured but terminal environment injection is disabled`
- This is a VS Code terminal setting warning.
- App still loads `backend/.env` via `pydantic-settings` in `config.py`.
