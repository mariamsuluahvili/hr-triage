FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    LLM_PROVIDER=mock \
    SCENARIO_ID=g03 \
    DB_PATH=/data/analyses.db

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-deps .

COPY scenarios ./scenarios
COPY ui ./ui

RUN useradd --system --create-home --uid 10001 appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /data /app

USER appuser

VOLUME ["/data"]
EXPOSE 8000 8501

CMD ["python", "-m", "uvicorn", "ticket_app.api:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
