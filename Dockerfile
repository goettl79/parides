# Use a very slim base image
FROM python:3.12-slim AS builder

# Set environment variables for Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install poetry
RUN pip install poetry==1.7.1

WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock README.md ./
COPY parides ./parides

# Install production dependencies and the project itself
RUN poetry install --only main

# Final Stage
FROM python:3.12-slim

WORKDIR /app

# Copy the virtual environment from the builder
COPY --from=builder /app/.venv /app/.venv
# Copy the source code as it might be needed by the venv (editable install)
COPY parides /app/parides

# Add the venv bin to PATH so 'parides' is available
ENV PATH="/app/.venv/bin:$PATH"

# Set the entrypoint to the parides CLI
ENTRYPOINT ["parides"]
