FROM ghcr.io/astral-sh/uv:latest AS uv_bin
FROM python:3.12-slim-bookworm

ENV CONFIG_PATH="/easy-gateway/easy_conf.yaml" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY --from=uv_bin /uv /uvx /bin/

WORKDIR /easy-gateway

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

CMD ["sh", "-c", "uv run --no-sync --frozen easy-gateway -c \"$CONFIG_PATH\""]
