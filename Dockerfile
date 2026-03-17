# Use a very slim base image
FROM python:3.12-slim as builder

# Set environment variables for Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install poetry
RUN pip install poetry==1.7.1

WORKDIR /app
COPY pyproject.toml poetry.lock ./
# Install only production dependencies
RUN poetry install --no-root --only main

# Final Stage
FROM python:3.12-slim

WORKDIR /app
# Copy the virtual environment from the builder
COPY --from=builder /app/.venv /app/.venv
COPY parides /app/parides

# Add the venv bin to PATH so 'parides' is available
ENV PATH="/app/.venv/bin:$PATH"

# Set the entrypoint to the parides CLI
ENTRYPOINT ["parides"]
