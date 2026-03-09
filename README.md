# Easy-Gateway Documentation

## Обзор

**Easy-Gateway** — легковесный API Gateway для микросервисной архитектуры.

### Возможности

- Простая настройка через YAML
- CLI интерфейс
- Система middleware
- Маршрутизация с префиксами
- Rate limiting (ограничение запросов)
- Логирование
- Кэширование

### Требования

- Python ≥ 3.7
- Без внешних зависимостей

### Версия

v0.1.4

---

## Установка

```bash
pip install easy-gateway
```

---

## Настройка конфигурации (config.yaml)

### 1. Настройки сервера

```yaml
server:
    host: "0.0.0.0"
    port: 8000
```

### 2. Настройки кэширования

```yaml
redis:
    enabled: true  # или false для InMemory Cache
    url: "redis://localhost:6379"
    expire_time: 500  # время жизни кэша в секундах (по умолчанию 180)
```

Для запуска Redis можно использовать Docker:
```bash
docker run -d --name my-redis -p 6379:6379 redis
```

### 3. Маршруты

```yaml
routes:
  - path: "/bin/*"
    target: "https://httpbin.org/"
    description: "Echo Server"
```

**Важно:**
- `path: "/user/*"` — для URL с любым префиксом после user
- `path: "/user/"` — для точного URL

### 4. Middleware

Доступные middleware:
- `LoggingMiddleware` — логирование запросов
- `RateLimitMiddleware` — ограничение частоты запросов

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

---

## Запуск

```bash
easy-gateway -c PATH-TO-YOUR-CONFIG
# или
easy-gateway --config
# или просто
easy-gateway  (если конфиг в корневой директории)
```

---

## Структура проекта

```
easy-gateway-docs/
├── index.html    # HTML страница документации
├── script.js     # JavaScript для навигации и копирования кода
├── styles.css    # Стили (тёмная тема)
└── README.md     # Этот файл
```

---

## Ссылки

- GitHub: https://github.com/MarkLevkovich/easy_gateway
