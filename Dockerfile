FROM python:3.12.4-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.2 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

ENV PATH="$POETRY_HOME/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set working directory
WORKDIR /app

# Copy only requirements files first for caching
COPY pyproject.toml poetry.lock* ./

# Install project dependencies
RUN poetry install --only main --no-root && \
    poetry cache clear --all pypi

# Copy the rest of the application
COPY . .

# Create and activate virtual environment
RUN poetry install --only-root

# Set the entrypoint to run through Poetry
ENTRYPOINT ["poetry", "run"]

# Default command to run the spider
CMD ["python", "/app/src/pipeline/extraction/spider.py"]
