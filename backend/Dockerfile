FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN mkdir -p app && touch app/__init__.py && \
    pip install --no-cache-dir . && rm -rf app

# 下載繁中大辭典 (584K 詞條)
RUN curl -sL https://raw.githubusercontent.com/fxsjy/jieba/master/extra_dict/dict.txt.big \
    -o data/dict.txt.big

RUN adduser --disabled-password --gecos '' appuser
COPY app/ app/
COPY data/ data/
USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; import os; urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\",8000)}/api/health')"

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4 --limit-concurrency 60
