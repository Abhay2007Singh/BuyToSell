# BuyToSell API

A RESTful e-commerce API built with FastAPI, featuring JWT authentication, role-based access control, Redis caching, WebSocket support, and async database operations.

## Tech Stack

- **FastAPI** — web framework
- **SQLAlchemy** + **Alembic** — ORM and migrations
- **SQLite** (dev) / **PostgreSQL** (prod via psycopg2/asyncpg)
- **Redis** — response caching
- **JWT** (python-jose) — authentication
- **slowapi** — rate limiting
- **pytest** — testing

## Project Structure

```
app/
├── main.py               # App entry point, middleware, router registration
├── database.py           # Sync DB session
├── async_database.py     # Async DB session
├── models/               # SQLAlchemy models (User, Product, Order, OrderItem)
├── schemas/              # Pydantic schemas
├── routers/              # Route handlers (auth, users, products, orders)
├── services/             # Business logic
├── utils/                # Security, Redis, storage, logging, background tasks
└── dependencies/         # Shared dependencies (pagination, auth guards)
alembic/                  # DB migrations
tests/                    # pytest test suite
```

## Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env   # edit values as needed

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | SQLAlchemy DB URL |
| `ASYNC_DATABASE_URL` | Async DB URL (asyncpg) |
| `SECRET_KEY` | JWT signing secret |
| `REDIS_URL` | Redis connection URL |

## API Endpoints

Base path: `/api/v1`

### Auth
| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login, returns JWT tokens |
| POST | `/auth/refresh` | Refresh access token |

### Users
| Method | Path | Auth |
|---|---|---|
| GET | `/users/` | Admin |
| GET | `/users/{id}` | Authenticated |
| PUT | `/users/{id}` | Owner / Admin |
| DELETE | `/users/{id}` | Admin |

### Products
| Method | Path | Auth |
|---|---|---|
| GET | `/products/` | Public |
| GET | `/products/{id}` | Public |
| POST | `/products/` | Seller / Admin |
| PUT | `/products/{id}` | Owner / Admin |
| DELETE | `/products/{id}` | Admin |
| POST | `/products/{id}/image` | Seller / Admin |

### Orders
| Method | Path | Auth |
|---|---|---|
| POST | `/orders/` | Customer / Admin |
| GET | `/orders/` | Authenticated |
| GET | `/orders/{order_id}` | Owner / Admin |
| GET | `/orders/user/{user_id}` | Owner / Admin |
| PUT | `/orders/{id}/status` | Admin |
| WS | `/orders/ws/orders/{order_id}` | Token required |

## User Roles

- **customer** — browse products, place and view own orders
- **seller** — create and manage own products
- **admin** — full access to all resources

## Features

- **JWT auth** with access + refresh tokens
- **Role-based access control** on all protected routes
- **Redis caching** on product listings (60s TTL, auto-invalidated on write)
- **WebSocket** real-time order status updates
- **Background tasks** — order confirmation email + stock deduction
- **Rate limiting** via slowapi
- **Request logging** middleware
- **Static file** serving (`/static`)
- **Health check** at `GET /health`

## Running Tests

```bash
pytest tests/
```

## API Docs

Interactive docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
