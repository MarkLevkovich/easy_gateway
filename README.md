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
    enabled: true      # false -> cache disabled
    url: "redis://localhost:6379"
    expire_time: 300   # cache TTL in seconds (default 180)
```

To run Redis, you can use Docker:
```bash
docker run -d --name my-redis -p 6379:6379 redis
```

Caching is **per-route** — add `cache: true` to any route to enable it (default `false`):

```yaml
routes:
  - path: "/pets/*"
    target: "https://petstore.swagger.io/"
    cache: true        # enable response caching for this route
```

**How caching works:**
- Only `GET` requests are cached — and only successful responses (`2xx`)
- Cache key: `cache:<path>:<METHOD>:<md5(query_params)>` — requests with different params never collide
- TTL is controlled by `redis.expire_time`
- Any non-`GET` request (POST/PUT/DELETE/PATCH) to a cached route automatically invalidates its cache entries
- Cache health is reported in `/health`

### 3. Routes

```yaml
routes:
  - path: "/bin/*"                 # prefix route: /bin/anything, /bin/ip, ...
    target: "https://httpbin.org/" # full URL, requested path is appended

  - path: "/users"                 # exact route: only /users
    target: "https://api.example.com"   # base URL, route path is appended automatically

  - path: "/pets/*"
    target: "https://petstore.swagger.io/"
    description: "Pets service"
    cache: true                    # enable response caching for this route
```

**Important:**
- `path: "/user/*"` — prefix route: forwards any `/user/...` path to the target
- `path: "/user/"` — exact route: matches only that URL
- For **exact** routes the target must be a **base URL without the path** — the route path is appended automatically (`/users` + `https://api.example.com` → `https://api.example.com/users`)
- For **prefix** routes the target must be a full URL (with `http://` or `https://`)
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