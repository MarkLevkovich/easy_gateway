# Easy-Gateway Documentation

## Overview

**Easy-Gateway** — lightweight API Gateway for microservices architecture.

### Features

- Simple YAML configuration
- CLI interface
- Middleware system
- Prefix-based routing
- Rate limiting
- Logging
- Caching
- Admin Panel with Basic Auth

### Requirements

- Python ≥ 3.10
- No external dependencies

---

## Installation

```bash
pip install easy-gateway
# or
uv add easy-gateway
```

---

## Configuration (easy_conf.yaml)

### 1. Server Settings

```yaml
server:
    host: "0.0.0.0"
    port: 8000
```

### 2. Cache Settings

```yaml
redis:
    enabled: true  # or false for InMemory Cache
    url: "redis://localhost:6379"
    expire_time: 500  # cache TTL in seconds (default 180)
```

To run Redis, you can use Docker:
```bash
docker run -d --name my-redis -p 6379:6379 redis
```

### 3. Routes

```yaml
routes:
  - path: "/bin/*"
    target: "https://httpbin.org/"
    description: "Echo Server"
```

**Important:**
- `path: "/user/*"` — for URLs with any prefix after user
- `path: "/user/"` — for exact URL match

### 4. Middleware

Available middleware:
- `LoggingMiddleware` — request logging
- `RateLimitMiddleware` — request rate limiting

```yaml
middlewares:
  - name: "LoggingMiddleware"
    enabled: true

  - name: "RateLimitMiddleware"
    enabled: true
    requests_per_minute: 5
```

### 5. CORS

```yaml
cors:
  allow_origins:
    - "myfront.com"
    - "testreact.space"
```

### 6. ADMIN
```yaml
admin:
  username: "jack" # by default: admin
  password: "2026" # by default: admin
```

---

## Running

```bash
easy-gateway -c PATH-TO-YOUR-CONFIG
# or simply
easy-gateway  (if config is in root directory)
```
---
