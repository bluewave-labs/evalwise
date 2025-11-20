# EvalWise

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15+-000000?logo=nextdotjs)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791?logo=postgresql)](https://postgresql.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178C6?logo=typescript)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)

A developer-friendly red teaming and evaluation platform for Large Language Models (LLMs).

## Features

- **Evaluations**: Built-in evaluators including LLM judges with ISO 42001 and EU AI Act rubrics
- **Red Teaming**: Basic jailbreak scenarios and adversarial testing
- **Datasets**: CSV/JSONL upload with version tracking
- **Metrics**: Pass rates, mean scores, and run comparisons
- **Playground**: Single prompt testing with immediate evaluation
- **Multi-Provider**: Support for OpenAI, Azure OpenAI, and OpenAI-compatible endpoints
- **Authentication**: JWT-based authentication with role-based access control
- **Security**: Password reset, rate limiting, session management, and audit logging

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)
- [License](#license)

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (v20.10+) and **Docker Compose** (v2.0+)
- **Make** (usually pre-installed on Linux/macOS)
- **Git** (for cloning the repository)
- *Optional*: **jq** (for testing API endpoints with `make test-api`)

## Quick Start

For a quick backend-only demo:

```bash
# Clone the repository
git clone <repository-url>
cd evalwise

# Create environment file
cp .env.example .env

# Edit .env and set required values (at minimum POSTGRES_PASSWORD)
nano .env

# Run the complete demo (migrations + seed data + start)
make demo

# Access the API
# API docs: http://localhost:8000/docs
# Health check: http://localhost:8000/health
```

For the full-stack application (Web UI + API):

```bash
# Create environment file
cp .env.example .env

# Edit .env and configure all required values
nano .env

# Start all services (web, api, worker, postgres, redis)
docker-compose up --build -d

# Run migrations
docker-compose exec api alembic upgrade head

# Create initial admin user
docker-compose exec api python -c "
from database import SessionLocal
from auth.models import User
from auth.security import get_password_hash

db = SessionLocal()
admin = User(
    username='admin',
    email='admin@example.com',
    hashed_password=get_password_hash('admin123'),
    is_superuser=True,
    is_active=True
)
db.add(admin)
db.commit()
print('Admin user created: username=admin, password=admin123')
"

# Access the application
# Web UI: http://localhost:3001
# API docs: http://localhost:8003/docs
```

## Installation

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd evalwise
```

### Step 2: Environment Configuration

Create your environment file from the template:

```bash
cp .env.example .env
```

Edit `.env` and configure the required variables:

**Critical (Required):**
```env
# Database - REQUIRED
POSTGRES_PASSWORD=your_secure_password_here
DATABASE_URL=postgresql://evalwise:your_secure_password_here@postgres:5432/evalwise

# Security - REQUIRED (generate with: openssl rand -hex 32)
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_here
API_ENCRYPTION_KEY=your_encryption_key_here
```

**Optional Configuration:**
```env
# LLM Provider API Keys (optional, needed for LLM judge evaluators)
OPENAI_API_KEY=sk-...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://...

# Email (optional, needed for password reset)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=noreply@yourdomain.com

# Environment
ENVIRONMENT=development  # or 'production'
DEBUG=true  # set to false in production
```

**Generate secure keys:**
```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate JWT_SECRET_KEY
openssl rand -hex 32

# Generate API_ENCRYPTION_KEY
openssl rand -hex 32
```

### Step 3: Choose Your Setup

#### Option A: Full Stack (Recommended)

Complete application with Web UI, API, Workers, Database, and Redis:

```bash
# Start all services
docker-compose up --build -d

# Run database migrations
docker-compose exec api alembic upgrade head

# Create admin user (see Quick Start section above)

# Verify all services are running
docker-compose ps

# View logs
docker-compose logs -f
```

Access points:
- **Web UI**: http://localhost:3001
- **API**: http://localhost:8003
- **API Docs**: http://localhost:8003/docs

#### Option B: Backend Only

API and database only (no Web UI):

```bash
# Start backend services
docker-compose -f docker-compose.simple.yml up --build -d

# Run database migrations
docker-compose -f docker-compose.simple.yml exec api alembic upgrade head

# Create admin user
docker-compose -f docker-compose.simple.yml exec api python -c "
from database import SessionLocal
from auth.models import User
from auth.security import get_password_hash

db = SessionLocal()
admin = User(
    username='admin',
    email='admin@example.com',
    hashed_password=get_password_hash('admin123'),
    is_superuser=True,
    is_active=True
)
db.add(admin)
db.commit()
print('Admin user created!')
"

# Or use make commands
make migrate  # Run migrations
make dev      # Start services
make seed     # Add demo data
```

Access points:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Step 4: Create Admin User

After starting services, create an admin user:

```bash
# For full stack
docker-compose exec api python -c "
from database import SessionLocal
from auth.models import User
from auth.security import get_password_hash

db = SessionLocal()
admin = User(
    username='admin',
    email='admin@example.com',
    hashed_password=get_password_hash('ChangeMe123!'),
    is_superuser=True,
    is_active=True
)
db.add(admin)
db.commit()
print('✓ Admin user created: admin / ChangeMe123!')
"

# Or for backend-only setup, replace 'docker-compose' with:
# docker-compose -f docker-compose.simple.yml
```

**Important**: Change the default password immediately after first login!

### Step 5: Verify Installation

```bash
# Check all services are healthy
docker-compose ps

# Test API health
curl http://localhost:8003/health

# Or for backend-only:
curl http://localhost:8000/health

# Login to get access token
curl -X POST http://localhost:8003/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"ChangeMe123!"}'
```

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

**Key Variables:**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_PASSWORD` | Yes | - | Database password |
| `SECRET_KEY` | Yes | - | Application secret key |
| `JWT_SECRET_KEY` | Yes | - | JWT signing key |
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `ENVIRONMENT` | No | `production` | `development` or `production` |
| `DEBUG` | No | `false` | Enable debug mode |
| `OPENAI_API_KEY` | No | - | OpenAI API key for LLM judges |
| `CORS_ORIGINS` | No | `["http://localhost:3001"]` | Allowed CORS origins |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No | `15` | Access token expiration |
| `MAX_LOGIN_ATTEMPTS` | No | `5` | Max failed login attempts |
| `SMTP_SERVER` | No | `localhost` | Email server for password reset |

### Docker Compose Files

- **`docker-compose.yml`**: Full stack (Web + API + Workers + DB + Redis)
- **`docker-compose.simple.yml`**: Backend only (API + DB + Redis)

## Usage

### Common Commands

```bash
# Using Make (backend-only setup)
make help        # Show all available commands
make dev         # Start development environment
make build       # Build all services
make migrate     # Run database migrations
make seed        # Seed database with demo data
make demo        # Complete demo setup
make logs        # Show API logs
make status      # Show container status
make clean       # Stop and remove all containers

# Using Docker Compose (full stack)
docker-compose up -d              # Start all services
docker-compose down               # Stop all services
docker-compose logs -f            # View logs
docker-compose logs -f web        # View web logs
docker-compose logs -f api        # View API logs
docker-compose ps                 # Check service status
docker-compose exec api bash      # Access API container
docker-compose restart api        # Restart API service
```

### API Authentication

All API endpoints (except `/auth/*` and `/health`) require authentication:

```bash
# 1. Login to get access token
TOKEN=$(curl -X POST http://localhost:8003/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"ChangeMe123!"}' \
  | jq -r '.access_token')

# 2. Use token in subsequent requests
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8003/datasets
```

### Creating Datasets

Upload a CSV or JSONL file with evaluation data:

```bash
# Create dataset
curl -X POST http://localhost:8003/datasets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Test Dataset",
    "tags": ["test"],
    "is_synthetic": false
  }'

# Upload items from CSV
curl -X POST http://localhost:8003/datasets/{dataset_id}/items \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@dataset.csv"
```

## Development

### Local Development Without Docker

**Backend:**

```bash
cd api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export DATABASE_URL="postgresql://user:pass@localhost:5432/evalwise"
export SECRET_KEY="your-secret-key"
export JWT_SECRET_KEY="your-jwt-key"

# Run migrations
alembic upgrade head

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**

```bash
cd web

# Install dependencies
npm install

# Set up environment variables
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev
```

### Running Tests

```bash
# Backend tests
cd api
pytest

# With coverage
pytest --cov=. --cov-report=html

# Frontend tests
cd web
npm test
```

### Code Quality

```bash
# Backend linting
cd api
black .
flake8 .

# Frontend linting
cd web
npm run lint
```

## Troubleshooting

### Common Issues

**1. Port already in use**

```bash
# Check what's using the port
sudo lsof -i :8003  # or :3001, :5432, :6379

# Change ports in docker-compose.yml or stop conflicting services
```

**2. Database connection errors**

```bash
# Ensure POSTGRES_PASSWORD is set in .env
# Check if PostgreSQL is healthy
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

**3. "POSTGRES_PASSWORD is required" error**

```bash
# Make sure .env file exists and contains:
POSTGRES_PASSWORD=your_password

# Make sure you're in the correct directory
pwd  # Should be /path/to/evalwise
```

**4. Migration errors**

```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d postgres redis
docker-compose exec api alembic upgrade head
```

**5. Authentication errors (401 Unauthorized)**

```bash
# Ensure you're using the access token from login response
# Token expires in 15 minutes by default
# Login again to get a fresh token
```

**6. Web UI can't connect to API**

```bash
# Check API is running
curl http://localhost:8003/health

# Verify NEXT_PUBLIC_API_URL in web/.env.local
# Should be: NEXT_PUBLIC_API_URL=http://localhost:8003
```

**7. Module import errors in API**

```bash
# Rebuild the API container
docker-compose build api
docker-compose up -d api
```

### Getting Help

```bash
# Check all service logs
docker-compose logs

# Check specific service
docker-compose logs api
docker-compose logs web

# Check service status
docker-compose ps

# Access container shell for debugging
docker-compose exec api bash
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Increase Docker resources in Docker Desktop settings:
# - Memory: 4GB minimum (8GB recommended)
# - CPUs: 2 minimum (4 recommended)
```

## Architecture

- **Backend**: FastAPI + PostgreSQL + Redis
- **Workers**: Celery for async evaluation jobs
- **Frontend**: Next.js 15 + TypeScript + TailwindCSS
- **Evaluators**: Local inference with transformers and sentence-transformers
- **Authentication**: JWT-based with refresh tokens
- **Security**: Rate limiting, session management, audit logging
- **Retention**: Automatic 90-day data purge

### Tech Stack

- **API**: Python 3.11, FastAPI, SQLAlchemy, Alembic
- **Database**: PostgreSQL 16
- **Cache/Queue**: Redis 7
- **Task Queue**: Celery
- **Web**: Next.js 15, React 18, TypeScript, TailwindCSS
- **ML**: Transformers, Sentence-Transformers, SpaCy, Presidio

## License

AGPLv3 - See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## Security

For security issues, please email security@yourdomain.com instead of using the issue tracker.