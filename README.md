# Autopedicare Backend

A FastAPI backend for vehicle and user management, built for automotive service workflows with Google-based identity, onboarding orchestration, RBAC, and vehicle ownership APIs.

## Overview

This backend powers a vehicle management and service platform where users can:

- sign in with Google accounts
- complete onboarding based on account type
- manage vehicles they own
- receive access and refresh tokens with secure rotation
- be assigned role-based permissions through an RBAC system
- have geolocation and device metadata captured during authentication

The API is exposed under the versioned prefix `/api/v1` and includes health checks and automatic OpenAPI docs via FastAPI.

## Target Backend Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                    API GATEWAY & SERVICE MESH                           │
│  (NGINX Ingress + TLS 1.3, Rate Limiting, Request Routing)              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────────────────────────┐    ┌──────────────────────┐   │
│  │   MODULAR MONOLITH BACKEND (Rust)    │    │   AI ENGINE (Python) │   │
│  │   (Axum + Tokio + SQLx)              │    │   (FastAPI)          │   │
│  │                                       │    │                      │   │
│  │  ┌──────────────────────────────┐    │    │  ┌─────────────────┐ │   │
│  │  │ Auth & Multi-Tenant RBAC     │    │    │  │ Vision Pipeline │ │   │
│  │  │ • JWT token validation       │    │    │  │ • YOLOv8        │ │   │
│  │  │ • Role enforcement           │    │    │  │ • ResNet50      │ │   │
│  │  │ • Permission caching         │    │    │  │ • ONNX Runtime  │ │   │
│  │  └──────────────────────────────┘    │    │  └─────────────────┘ │   │
│  │  ┌──────────────────────────────┐    │    │  ┌─────────────────┐ │   │
│  │  │ Rescue Dispatch Engine       │    │    │  │ Behavioral ML   │ │   │
│  │  │ • GPS location service       │    │    │  │ • Wear modeling │ │   │
│  │  │ • Operator matching (spatial)│    │    │  │ • Risk scoring  │ │   │
│  │  │ • Job state machine          │    │    │  │ • Recommendations│ │   │
│  │  │ • WebSocket driver tracking  │    │    │  └─────────────────┘ │   │
│  │  └──────────────────────────────┘    │    │                      │   │
│  │  ┌──────────────────────────────┐    │    │                      │   │
│  │  │ E-Commerce & Inventory       │    │    │                      │   │
│  │  │ • Multi-vendor catalog sync  │    │    │                      │   │
│  │  │ • Order management           │    │    │                      │   │
│  │  │ • Inventory real-time updates│    │    │                      │   │
│  │  │ • Checkout service           │    │    │                      │   │
│  │  └──────────────────────────────┘    │    │                      │   │
│  │  ┌──────────────────────────────┐    │    │                      │   │
│  │  │ Fleet & Wallet Service       │    │    │                      │   │
│  │  │ • Fleet registry management  │    │    │                      │   │
│  │  │ • Driver authorization       │    │    │                      │   │
│  │  │ • Wallet ledger transactions │    │    │                      │   │
│  │  │ • Spending approval workflow │    │    │                      │   │
│  │  └──────────────────────────────┘    │    │                      │   │
│  │  ┌──────────────────────────────┐    │    │                      │   │
│  │  │ Payment Abstraction          │    │    │                      │   │
│  │  │ • Paystack integration       │    │    │                      │   │
│  │  │ • Flutterwave fallback       │    │    │                      │   │
│  │  │ • Corporate wallet debit     │    │    │                      │   │
│  │  │ • Receipt generation         │    │    │                      │   │
│  │  └──────────────────────────────┘    │    │                      │   │
│  └──────────────────────────────────────┘    └──────────────────────┘   │
│                                                                           │
├─────────────────────────────────────────────────────────────────────────┤
│                         PERSISTENCE LAYER                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────────┐    ┌──────────────────────┐    ┌────────────┐ │
│  │  PostgreSQL 16       │    │  Redis Cluster       │    │ Vector DB  │ │
│  │  • Core OLTP DB      │    │  • Session cache     │    │ (Qdrant)   │ │
│  │  • PostGIS spatial   │    │  • Rate limiting     │    │ • Part     │ │
│  │  • pgvector          │    │  • Real-time queues  │    │   embeddings│ │
│  │  • JSON/JSONB        │    │  • Pub/Sub tracking  │    │            │ │
│  └──────────────────────┘    └──────────────────────┘    └────────────┘ │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### Extended platform modules to target

This repository already contains the foundational authentication and ownership-building blocks for a larger platform. The architecture can evolve naturally into the following service areas:

- Auth & Multi-Tenant RBAC
  - JWT validation and refresh token rotation
  - permission-based access control
  - tenant-aware user isolation
- Rescue Dispatch Engine
  - GPS-based service matching
  - work order lifecycle tracking
  - driver/operator assignment and job state transitions
- E-Commerce & Inventory
  - product and catalog synchronization
  - order processing
  - inventory availability tracking
- Fleet & Wallet Service
  - fleet registry and authorization
  - wallet ledger / spending controls
  - approval workflows for expense and disbursement events
- Payment Abstraction
  - Paystack integration and Flutterwave fallback
  - payment receipts and reconciliation
- AI Engine
  - vision models for vehicle and asset analysis
  - behavioral risk and recommendation scoring
  - embedding and similarity matching for catalog or inventory use cases

### Architecture alignment with this backend

The current FastAPI backend already provides the core security and domain foundation for this broader system:

- user authentication and access token validation
- onboarding and role assignment flow
- vehicle ownership and resource access boundaries
- geolocation-aware request context
- Redis-backed caching and request observability

These building blocks are the base for expanding into a modular monolith or a service-oriented platform without breaking the current codebase.

## Technology Stack (Backend)

| Component | Technology | Rationale |
| --- | --- | --- |
| Core Runtime | Rust (Axum + Tokio) | Memory safety, high concurrency, efficient handling for large live systems |
| Web Framework | Axum | Lightweight async API framework for modular service development |
| Database Driver | SQLx | Compile-time checked queries and type-safe database access |
| Async Runtime | Tokio | Non-blocking I/O for GPS tracking, real-time queues, and WebSockets |
| Database | PostgreSQL 16 | Proven OLTP performance, PostGIS, and JSONB support |
| Cache / Pub-Sub | Redis Cluster | Session cache, rate limiting, message queues, tracking |
| Vector DB | Qdrant | Similarity search and embeddings for catalog or asset matching |
| AI Inference | Python 3.12 + FastAPI | Model serving layer for vision and recommendation systems |
| ML Frameworks | PyTorch + ONNX | Training and deployment of inference models |
| Container | Docker | Reproducible local and cloud deployment environments |
| Orchestration | Kubernetes | Auto-scaling, service discovery, and rolling rollout support |
| Monitoring | Prometheus + Grafana | Real-time metrics and system observability |
| Logging | ELK Stack | Centralized logs and audit trail visibility |
| Message Queue | Redis Streams / RabbitMQ | Async processing of background jobs and distributed tasks |

## Implemented Features

### Authentication and user identity

- Google OAuth 2.0 sign-in using Google ID token verification
- JWT-based access tokens and refresh tokens
- Refresh token rotation and revocation support
- Bearer-token authentication with `get_current_user`
- Active-user enforcement before access is granted
- Login history capture with IP, device, OS, browser, geolocation, and request metadata
- Request trace ID generation and middleware-based context logging

### Onboarding and account types

- Supported onboarding account types:
  - `car_owner`
  - `vendor`
- Car owners are auto-approved and assigned the `car_owner` role
- Vendor onboarding remains pending for admin review
- Onboarding state is stored in `onboarding_requests`
- `assigned_role_id` is linked to the assigned role once approved

### RBAC and permissions

The system seeds a role and permission model with the following roles:

- `car_owner`
- `mechanic`
- `company`
- `admin`
- `commerce_admin`
- `product_manager`
- `inventory_manager`
- `order_manager`
- `superadmin`

Role and permission definitions are created by the RBAC seeding process, including permissions such as:

- `view_own_profile`
- `update_own_profile`
- `view_own_vehicles`
- `create_vehicle`
- `update_own_vehicle`
- `delete_own_vehicle`
- `review_onboarding`
- `assign_roles`
- `manage_roles`
- `manage_permissions`
- `manage_products`
- `manage_inventory`
- `manage_orders`
- `view_commerce_ledger`
- and additional admin/company/mechanic permissions

### Commerce and ecommerce operations

The backend now includes a working commerce domain with product management, inventory tracking, cart workflows, checkout, and admin oversight.

- Product catalog CRUD with SKU validation and status management
- Inventory records linked to products with stock thresholds and reservations
- User cart lifecycle with add-to-cart and total calculation
- Checkout flow that validates stock and creates orders with shipping details
- Order history for authenticated users
- Search index for catalog discovery using product name, description, category, brand, and SKU data
- Product recommendations using popularity and category-based relevance scoring
- Commerce ledger endpoint for superadmins to review transaction and order totals

Key endpoints:

- GET /api/v1/commerce/products
- GET /api/v1/commerce/products/search?q=phone&category=electronics
- GET /api/v1/commerce/products/recommendations?category=electronics&limit=5
- POST /api/v1/commerce/products
- POST /api/v1/commerce/products/{product_id}/inventory
- GET /api/v1/commerce/cart
- POST /api/v1/commerce/cart/items
- POST /api/v1/commerce/checkout
- GET /api/v1/commerce/orders
- GET /api/v1/commerce/admin/ledger

### Vehicle management

- Create vehicle records for the authenticated owner
- List vehicles for the current user with pagination
- Fetch a single vehicle with ownership validation
- Update vehicle details using partial PATCH updates
- Delete vehicles with ownership validation
- Unique VIN and license plate checks by database schema constraints

### Security and operational features

- HTTP bearer scheme enforcement
- Role- and permission-check dependencies (`require_role`, `require_permission`)
- Refresh token hashing before storage
- Token family tracking for refresh-token rotation and reuse prevention
- Redis-backed geolocation cache for IP lookup optimization
- Logging middleware for request timing and request ID propagation
- Health endpoints for liveness and readiness checks

## Tech Stack

- Python 3.13+
- FastAPI
- SQLAlchemy 2.0 + async PostgreSQL support
- Redis
- JWT via `python-jose`
- Google Auth library
- Pydantic + Pydantic Settings
- Alembic for migrations
- Docker and Docker Compose support

## Project Structure

```text
app/
├── auth/
│   ├── geolocation.py
│   ├── google.py
│   ├── models.py
│   ├── router.py
│   ├── schemas.py
│   ├── security.py
│   └── service.py
├── core/
│   ├── context.py
│   ├── logging.py
│   ├── middleware.py
│   └── redis.py
├── onboarding/
│   ├── models.py
│   ├── schemas.py
│   └── services.py
├── rbac/
│   ├── models.py
│   ├── seed.py
│   └── service.py
├── users/
│   └── models.py
├── vehicles/
│   ├── models.py
│   ├── router.py
│   ├── schemas.py
│   └── services.py
├── config.py
├── database.py
├── dependencies.py
├── exceptions.py
├── main.py
├── permissions.py
└── __init__.py
```

## Environment Configuration

Create a `.env` file in the project root with the required values:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/autopedicare
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

SECRET_KEY=change-me-to-a-secure-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

IP_API_KEY=your_ip_api_key
GEO_IP_API_URL=https://ipapi.co

REDIS_URL=redis://localhost:6379/0

GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### Notes

- The application expects a PostgreSQL database reachable via `DATABASE_URL`.
- Redis is used for geolocation caching and request metadata support.
- Google client values must match your OAuth client configuration in Google Cloud Console.

## Installation

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up the `.env` file as described above.
5. Run database migrations or initialize the schema.

## Database Setup

The project includes Alembic migrations in the `migrations/` directory.

```bash
alembic upgrade head
```

If you are setting up the database from scratch, make sure PostgreSQL is running and the configured database exists.

## Running the API

### Local development

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The app will be available at:

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Docker Compose

```bash
docker compose up --build
```

This starts the Redis service and runs the API container. The API is exposed on port 8000.

## Health and Debug Endpoints

### Root

```http
GET /
```

Returns a simple API welcome payload.

### Health

```http
GET /health
GET /health/live
GET /health/ready
```

These endpoints report the API health state and readiness.

### Debug context

```http
GET /debug/context
```

Returns the request context currently assembled by middleware, including client metadata and geolocation when available.

## API Endpoints

All routes below are mounted under `/api/v1` unless otherwise noted.

### Authentication endpoints

#### POST `/api/v1/auth/google`

Google login flow.

Request body:

```json
{
  "id_token": "google-id-token",
  "requested_type": "car_owner"
}
```

Supported values for `requested_type`:

- `car_owner`
- `vendor`

Response:

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "is_new_user": true
  },
  "onboarding": {
    "requested_type": "car_owner",
    "status": "approved",
    "assigned_role": "car_owner"
  },
  "tokens": {
    "access_token": "jwt-access-token",
    "refresh_token": "jwt-refresh-token",
    "token_type": "bearer"
  }
}
```

#### POST `/api/v1/auth/refresh`

Refresh an expired or soon-to-expire access token using a valid refresh token.

Request body:

```json
{
  "refresh_token": "refresh-token"
}
```

#### POST `/api/v1/auth/revoke`

Revokes a refresh token and returns `204 No Content`.

Request body:

```json
{
  "refresh_token": "refresh-token"
}
```

### Vehicle endpoints

All vehicle endpoints require a valid bearer access token.

#### POST `/api/v1/vehicles`

Create a vehicle owned by the authenticated user.

Request body:

```json
{
  "make": "Toyota",
  "model": "Corolla",
  "year": 2022,
  "vin": "1HGCM82633A004352",
  "license_plate": "ABC123",
  "color": "silver"
}
```

#### GET `/api/v1/vehicles`

List vehicles for the current user with pagination.

Query parameters:

- `offset` (default: `0`)
- `limit` (default: `20`, min: `1`, max: `100`)

#### GET `/api/v1/vehicles/{vehicle_id}`

Fetch a specific vehicle by ID. Access is restricted to the vehicle owner.

#### PATCH `/api/v1/vehicles/{vehicle_id}`

Update a vehicle. Only the authenticated owner can patch it.

Example:

```json
{
  "color": "black",
  "license_plate": "XYZ987"
}
```

#### DELETE `/api/v1/vehicles/{vehicle_id}`

Delete a vehicle. Returns `204 No Content` after successful deletion.

## Authentication Flow

1. Client sends a Google ID token to `/api/v1/auth/google`.
2. The server verifies the token using Google OAuth validation.
3. The user is created if they do not already exist.
4. The system resolves or creates an onboarding record.
5. Onboarding is processed:
   - `car_owner` → auto-approved and assigned role
   - `vendor` → kept pending for review
6. A login event is recorded with request metadata and IP-based geolocation.
7. A JWT access token and refresh token pair are generated.
8. The returned refresh token is stored using a SHA-256 hash and tracked by token family.

## Token Behavior

### Access token

- used for authenticated API requests
- short-lived (configured by `ACCESS_TOKEN_EXPIRE_MINUTES`)
- contains subject ID and token type

### Refresh token

- used to mint a new access token
- hashed before DB persistence
- rotated on refresh to prevent replay and token theft
- revoke endpoint marks a refresh token as invalid and blocks reuse

## RBAC Behavior

The backend exposes custom dependencies that check user authorization before endpoints are accessed.

- `get_current_user` validates the bearer token and loads the user
- `require_role(role_name)` ensures the user has a specific role
- `require_permission(permission_name)` ensures the user has a specific permission

This pattern is designed to protect admin, company, mechanic, and vehicle-management features as the project expands.

## Middleware and Context Tracking

The application includes a `UserContextMiddleware` that:

- reads the source IP address
- detects device type, OS, and browser from the user agent
- attempts geolocation resolution using the configured IP lookup service
- attaches a request ID to the request context
- logs request duration and response status

This is used during authentication for login history and for operational diagnostics.

## Example end-to-end ecommerce flow in Postman

The fastest way to exercise the full commerce flow is to follow this sequence in order.

### 1. Sign in and get tokens

Request:

```http
POST /api/v1/auth/google
Content-Type: application/json
```

Body:

```json
{
  "id_token": "google-id-token",
  "requested_type": "car_owner"
}
```

Save the returned `access_token` and `refresh_token` in the Postman collection variables. The collection already does this automatically for the auth requests.

> Use a user account that has the required commerce permissions such as `commerce_admin`, `product_manager`, `inventory_manager`, or `superadmin`.

### 2. Create a product

Request:

```http
POST /api/v1/commerce/products
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

Body:

```json
{
  "sku": "SKU-1001",
  "name": "Auto Care Kit",
  "description": "Essential maintenance kit for vehicle care.",
  "category": "automotive",
  "brand": "Autopedicare",
  "price": 2500,
  "image_url": "https://example.com/product.png",
  "status": "active"
}
```

If the request succeeds, save the returned product `id` into the `product_id` collection variable.

### 3. Add inventory for the product

Request:

```http
POST /api/v1/commerce/products/{{product_id}}/inventory
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

Body:

```json
{
  "product_id": "{{product_id}}",
  "quantity": 25,
  "low_stock_threshold": 5,
  "location": "warehouse-lagos"
}
```

### 4. Search the catalog

Request:

```http
GET /api/v1/commerce/products/search?q=care&category=automotive
Authorization: Bearer {{access_token}}
```

Expected behavior:

- returns a ranked list of products matching the search terms
- supports product name, category, SKU, brand, and description matching
- includes a `score` value used for search relevance

### 5. Get recommendations

Request:

```http
GET /api/v1/commerce/products/recommendations?category=automotive&limit=5
Authorization: Bearer {{access_token}}
```

Expected behavior:

- returns the most relevant product suggestions for the category
- uses popularity and recommendation scoring for ordering
- supports `product_id` and `category` filters

### 6. Get or create a cart

Request:

```http
GET /api/v1/commerce/cart
Authorization: Bearer {{access_token}}
```

Save the returned cart `id` in the `cart_id` variable.

### 7. Add an item to the cart

Request:

```http
POST /api/v1/commerce/cart/items
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

Body:

```json
{
  "product_id": "{{product_id}}",
  "quantity": 1
}
```

### 8. Checkout the cart

Request:

```http
POST /api/v1/commerce/checkout
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

Body:

```json
{
  "cart_id": "{{cart_id}}",
  "shipping_address": "14 Marina Road, Lagos, Nigeria",
  "notes": "Fragile packaging requested"
}
```

A successful checkout returns an order with:

- subtotal
- shipping fee
- total amount
- payment reference
- payment status
- order item list

### 9. View order history

Request:

```http
GET /api/v1/commerce/orders?offset=0&limit=20
Authorization: Bearer {{access_token}}
```

### 10. Review the commerce ledger as a superadmin

Request:

```http
GET /api/v1/commerce/admin/ledger
Authorization: Bearer {{access_token}}
```

This route is intended for users in the `superadmin` role and exposes the order-based commerce ledger summary for finance and oversight use.

## Current Implementation Notes

- Google authentication is the active login path in production.
- The schema layer includes an Apple auth request model, but there is no currently exposed Apple sign-in route in the router layer.
- The RBAC system is prepared for future endpoints beyond vehicle management and onboarding review.
- The app is structured to be extended with additional service modules, admin dashboards, and domain-specific workflows.

## Recommended Next Steps

Possible expansion areas for this project include:

- admin onboarding review endpoints
- user profile and status management
- service requests for mechanics and companies
- company-specific service workflows
- stricter role-scoped endpoint protection beyond the current vehicle routes
- automated tests for auth, token rotation, and RBAC enforcement

## API Documentation

FastAPI automatically generates interactive docs:

- Swagger UI: `/docs`
- Redoc: `/redoc`
- OpenAPI schema: `/openapi.json`

## License

This project currently does not specify a formal license. If you plan to open-source or distribute the backend, add a `LICENSE` file and document the licensing terms explicitly.
