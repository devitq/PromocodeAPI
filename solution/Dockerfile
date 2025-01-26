# Stage 1: Install dependencies
FROM docker.io/python:3.11-alpine3.20 AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.4.30 /uv /uvx /bin/

# Set the working directory
WORKDIR /app

# Setup env vars
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONOPTIMIZE=2 \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

# Copy pyproject.toml file
COPY pyproject.toml .

# Install dependencies
RUN uv sync --no-dev --no-install-project --no-cache


# Stage 2: Serve the application
FROM docker.io/python:3.11-alpine3.20

# Set the working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY . .

# Create app user and set permissions
RUN adduser -D -g '' app && chown -R app:app ./

# Run as non-root user
USER app

# Setup env vars
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONOPTIMIZE=2 \
    PATH="/opt/venv/bin:$PATH"

# Expose port
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:8080/health/?format=json || exit 1

# Set env vars for app (sorry for that)
ENV DJANGO_DEBUG=False \
    DJANGO_ALLOWED_HOSTS=*

# Start gunicorn
CMD python manage.py migrate && gunicorn config.wsgi -b ${SERVER_ADDRESS}
