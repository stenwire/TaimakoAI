# =============================================================================
# FRONTEND — build stages
# =============================================================================

FROM node:20-alpine AS frontend-deps
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

FROM frontend-deps AS frontend-builder
WORKDIR /app
COPY frontend/ .

ARG NEXT_PUBLIC_ENVIRONMENT
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_BACKEND_URL_PROD
ARG NEXT_PUBLIC_FRONTEND_URL_PROD
ARG NEXT_PUBLIC_BACKEND_URL_STAGING
ARG NEXT_PUBLIC_FRONTEND_URL_STAGING
ARG NEXT_PUBLIC_BACKEND_URL_DEV
ARG NEXT_PUBLIC_FRONTEND_URL_DEV

ENV NEXT_PUBLIC_ENVIRONMENT=$NEXT_PUBLIC_ENVIRONMENT \
    NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_BACKEND_URL_PROD=$NEXT_PUBLIC_BACKEND_URL_PROD \
    NEXT_PUBLIC_FRONTEND_URL_PROD=$NEXT_PUBLIC_FRONTEND_URL_PROD \
    NEXT_PUBLIC_BACKEND_URL_STAGING=$NEXT_PUBLIC_BACKEND_URL_STAGING \
    NEXT_PUBLIC_FRONTEND_URL_STAGING=$NEXT_PUBLIC_FRONTEND_URL_STAGING \
    NEXT_PUBLIC_BACKEND_URL_DEV=$NEXT_PUBLIC_BACKEND_URL_DEV \
    NEXT_PUBLIC_FRONTEND_URL_DEV=$NEXT_PUBLIC_FRONTEND_URL_DEV

RUN npm run build

FROM node:20-alpine AS frontend
WORKDIR /app

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

COPY --from=frontend-builder /app/public ./public
COPY --from=frontend-builder /app/.next/standalone ./
COPY --from=frontend-builder /app/.next/static ./.next/static

RUN chown -R nextjs:nodejs /app
USER nextjs

ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME="0.0.0.0"

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1

CMD ["node", "server.js"]


# =============================================================================
# BACKEND — build stages
# =============================================================================

FROM python:3.10-slim AS backend-builder
WORKDIR /app

RUN pip install --no-cache-dir uv
ENV UV_HTTP_TIMEOUT=300

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-cache

FROM python:3.10-slim AS backend
WORKDIR /app

RUN pip install --no-cache-dir uv

COPY --from=backend-builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY backend/ .

RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app && \
    chmod +x /app/start.sh
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["/app/start.sh"]
