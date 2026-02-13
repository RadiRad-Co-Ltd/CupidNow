FROM python:3.12-slim

WORKDIR /app

# Install CPU-only PyTorch first (smaller than default CUDA build)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy project metadata and install dependencies (cache layer)
COPY pyproject.toml .
RUN mkdir -p app && touch app/__init__.py && \
    pip install --no-cache-dir . && \
    rm -rf app

# Pre-download CKIP albert-tiny model so it's baked into the image
RUN python -c "from ckip_transformers.nlp import CkipWordSegmenter; CkipWordSegmenter(model='albert-tiny', device=-1)"

RUN adduser --disabled-password --gecos '' appuser

# Copy application code and data
COPY app/ app/
COPY data/ data/

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; import os; urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\",8000)}/api/health')"

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
