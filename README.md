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
    enabled: true      # false -> in-memory cache (resets on restart)
    url: "redis://localhost:6379"
    expire_time: 300   # cache TTL in seconds (default 180)
```

To run Redis, you can use Docker:
```bash
docker run -d --name my-redis -p 6379:6379 redis
```

### 3. Routes

```yaml
routes:
  - path: "/bin/*"                 # any path starting with /bin
    target: "https://httpbin.org/"
    description: "HTTPBin playground"

  - path: "/users"                 # exact match only
    target: "https://api.example.com/users"
    description: "Exact path -> full target URL"

  - path: "/pets/*"
    target: "https://petstore.swagger.io"
    description: "Pets service"
    cache: true                    # enable response caching for this route
```

**Important:**
- `path: "/user/*"` — for URLs with any prefix after user
- `path: "/user/"` — for exact URL match
- `cache: true` — (optional) enables response caching for a given route

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
    requests_per_minute: 30
```

### 5. CORS

```yaml
cors:
  allow_origins:
    - "https://myfront.com"
    - "https://testreact.space"
```

### 6. ADMIN
```yaml
admin:
  username: "admin" # by default: admin
  password: "admin" # change this in production!
```

---

## Running

```bash
easy-gateway -c PATH-TO-YOUR-CONFIG
# or simply
easy-gateway  (if config is in root directory)
```
---
