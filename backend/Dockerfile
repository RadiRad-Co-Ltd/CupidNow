FROM python:3.12-slim

WORKDIR /app

# Copy project metadata and install dependencies first (cache layer)
COPY pyproject.toml .
# Create minimal package structure so pip install . can resolve deps
RUN mkdir -p app && touch app/__init__.py && \
    pip install --no-cache-dir . && \
    rm -rf app

RUN adduser --disabled-password --gecos '' appuser

# Copy actual application code
COPY app/ app/

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
