FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/app/config/settings.py /app/backend/app/config/settings.py
# In actual setups we install poetry/pip-tools, here we install core dependencies directly
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    celery \
    redis \
    sqlalchemy \
    pydantic-settings \
    pydantic \
    networkx \
    pytest \
    pytest-asyncio \
    pytest-cov \
    ruff

# Copy codebase
COPY . /app/

ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
