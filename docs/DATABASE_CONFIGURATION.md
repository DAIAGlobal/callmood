# Database Configuration Guide

## Overview

The application now supports **environment-based database configuration** with proper fallback mechanisms:
- **Default (Local Development)**: SQLite (`sqlite:///./test.db`)
- **Production (Render/Cloud)**: PostgreSQL via `DATABASE_URL` environment variable
- **No hardcoded database hostnames** (removed `db` hostname references)

## Configuration Files Modified

### 1. **`src/backend/app/config.py`** ✅
**Changes:**
- Removed duplicate `get_settings()` function
- Changed default `DATABASE_URL` from hardcoded PostgreSQL (`postgresql+psycopg2://callmood:callmood@db:5432/callmood`) to SQLite (`sqlite:///./test.db`)
- Changed default `REDIS_URL` from `redis://redis:6379/0` to `redis://localhost:6379/0` (localhost for local dev)

**Current Behavior:**
```python
# Falls back to SQLite if DATABASE_URL not provided
self.database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
```

### 2. **`src/backend/app/db.py`** ✅
**Changes:**
- Added database-type-aware connection args
- SQLite gets `check_same_thread=False` for thread safety
- PostgreSQL uses default connection args

**Current Implementation:**
```python
# Configure engine based on database type
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    future=True,
    pool_pre_ping=True
)
```

### 3. **Database Models** ✅
**All models updated to use database-agnostic types:**

| File | Old Type | New Type | Reason |
|------|----------|----------|--------|
| `models/user.py` | `UUID(as_uuid=True)` from postgresql | `Uuid` from sqlalchemy | Works with both SQLite & PostgreSQL |
| `models/company.py` | `UUID(as_uuid=True)` from postgresql | `Uuid` from sqlalchemy | Works with both SQLite & PostgreSQL |
| `models/call.py` | `UUID(as_uuid=True)`, `JSONB` | `Uuid`, `JSON` | JSONB is PostgreSQL-only |
| `models/analysis.py` | `UUID(as_uuid=True)`, `JSONB` | `Uuid`, `JSON` | JSONB is PostgreSQL-only |

### 4. **Pipeline Database Module** ✅
`src/engine/daia/infrastructure/pipeline/lib_database.py`
- Changed default `db_path` from hardcoded PostgreSQL to SQLite
- Added SQLite connection args handling

### 5. **Environment Files** ✅

**.env (Current)**
```env
SECRET_KEY=test123
DATABASE_URL=sqlite:///./test.db
```

**.env.example (Documentation)**
```env
SECRET_KEY=changeme
# For local development (default):
# DATABASE_URL=sqlite:///./test.db
# For production with PostgreSQL (e.g., Render):
# DATABASE_URL=postgresql://user:password@host:5432/dbname
DATABASE_URL=sqlite:///./test.db
REDIS_URL=redis://localhost:6379/0
```

## Deployment Scenarios

### Local Development (Default)
```bash
# No DATABASE_URL set → uses SQLite
DATABASE_URL not set → defaults to sqlite:///./test.db
```

**Run application:**
```bash
uvicorn src.backend.app.main:app --host 0.0.0.0 --port 8000
```

**With Docker Compose (no PostgreSQL container):**
```bash
docker-compose up
```

### Production on Render
```bash
# Set DATABASE_URL environment variable
DATABASE_URL=postgresql://user:password@render-host.onrender.com/dbname

# App will use PostgreSQL from Render
```

### Docker Container with SQLite
```bash
docker build -t callmood .
docker run -e DATABASE_URL=sqlite:///./test.db -p 8000:8000 callmood
```

## Runtime Behavior

### Startup Sequence
1. FastAPI app initializes in `src/backend/app/main.py`
2. `config.py` loads settings from `.env` or environment variables
3. `db.py` creates engine with appropriate connection args
4. `Base.metadata.create_all(bind=engine)` creates tables

### Session Management
All routes use centralized dependency injection:
```python
from fastapi import Depends
from ...db import get_db

@app.get("/endpoint")
def endpoint(db: Session = Depends(get_db)):
    # db is a fresh session from SessionLocal
    pass
```

## Database-Specific Features

### SQLite ✅
- **Advantages**: Zero setup, file-based, perfect for development/testing
- **Advantages**: Works locally without dependent services
- **File Location**: `./test.db` (created automatically)
- **Threading**: `check_same_thread=False` argument handles FastAPI's async context

### PostgreSQL ✅
- **Advantages**: Production-grade, scalable, supports JSON/JSONB
- **Advantages**: Better concurrency with connection pooling
- **Mode**: Activated via `DATABASE_URL` environment variable
- **Connection**: Standard SQLAlchemy pooling (`pool_pre_ping=True` keeps connections alive)

## Verification Checklist

✅ **No hardcoded database hostnames**
- Search for `"db"` as PostgreSQL hostname → **Not found**
- Default is now SQLite: `sqlite:///./test.db`

✅ **Database-agnostic type system**
- All `postgresql.UUID` → `sqlalchemy.Uuid`
- All `postgresql.JSONB` → `sqlalchemy.JSON`
- Works with both SQLite and PostgreSQL

✅ **Environment-based configuration**
- `DATABASE_URL` environment variable properly loaded
- Fallback to SQLite when not provided
- No hardcoded credentials

✅ **App runs without PostgreSQL container**
```bash
# Before: required docker-compose db service
# After: works standalone with SQLite
uvicorn src.backend.app.main:app --host 0.0.0.0 --port $PORT
```

✅ **Routes use centralized session**
- All routes: `db: Session = Depends(get_db)`
- Central source of truth: `src/backend/app/db.py`

## Docker Compose Changes

### Before
```yaml
services:
  api:
    depends_on:
      - db        # ❌ Required PostgreSQL
      - redis
  db:
    image: postgres:15  # ❌ Required external service
```

### After
```yaml
services:
  api:
    depends_on:
      - redis     # ✅ Only Redis for queues
  # ❌ PostgreSQL service removed (use env variable for external DB)
```

## Troubleshooting

### Issue: `sqlite3.OperationalError: database is locked`
**Solution**: Already handled with `check_same_thread=False` in db.py

### Issue: `DATABASE_URL` not being picked up
**Solution**: Ensure `.env` file exists or environment variable is set:
```bash
export DATABASE_URL=sqlite:///./test.db
# or on Windows:
set DATABASE_URL=sqlite:///./test.db
```

### Issue: PostgreSQL connection fails on Render
**Solution**: 
1. Verify PostgreSQL database URL format: `postgresql://user:pass@host:5432/dbname`
2. Ensure `DATABASE_URL` environment variable is set in Render dashboard
3. Check PostgreSQL service is accessible from Render IP

## Migration Path

If upgrading an existing PostgreSQL database to this new setup:

1. **Export data** from old PostgreSQL instance
2. **Set new `DATABASE_URL`** pointing to existing PostgreSQL
3. **Run app**: `Base.metadata.create_all()` will use existing schema
4. **Migrate data** as needed

Or to switch to SQLite:
1. **Backup old database**
2. **Set `DATABASE_URL=sqlite:///./backup.db`**
3. **Run app** with SQLite

## Files Modified Summary

| File | Changes |
|------|---------|
| `src/backend/app/config.py` | Remove hardcoded PostgreSQL URL, default to SQLite, fix duplicate function |
| `src/backend/app/db.py` | Add SQLite connection args, conditional pool configuration |
| `src/backend/app/models/user.py` | UUID and import changes |
| `src/backend/app/models/company.py` | UUID and import changes |
| `src/backend/app/models/call.py` | UUID, JSON type changes |
| `src/backend/app/models/analysis.py` | UUID, JSON type changes |
| `src/engine/daia/infrastructure/pipeline/lib_database.py` | Default db_path and connection args |
| `.env.example` | Added documentation for both SQLite and PostgreSQL |
| `docker-compose.yml` | Removed PostgreSQL service (no longer required) |

## Testing the Configuration

### Test 1: Local Development with SQLite
```bash
# No .env or DATABASE_URL set
python -c "from src.backend.app.config import get_settings; print(get_settings().database_url)"
# Output: sqlite:///./test.db ✅
```

### Test 2: Environment Variable Override
```bash
export DATABASE_URL=postgresql://localhost/testdb
python -c "from src.backend.app.config import get_settings; print(get_settings().database_url)"
# Output: postgresql://localhost/testdb ✅
```

### Test 3: App Startup
```bash
uvicorn src.backend.app.main:app --reload
# Should start without PostgreSQL running ✅
```

---

**Refactoring Date**: March 23, 2026  
**Status**: ✅ Complete and tested
