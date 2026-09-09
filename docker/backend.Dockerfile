FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY migrations ./migrations
COPY scripts ./scripts
COPY alembic.ini ./
RUN python -m pip install --no-cache-dir --upgrade "pip>=26.2" \
    && pip install --no-cache-dir .
RUN groupadd --system projectbet && useradd --system --gid projectbet --home-dir /app projectbet \
    && chown -R projectbet:projectbet /app
USER projectbet
CMD ["sh", "-c", "alembic upgrade head && uvicorn brain_projectbet.api.main:app --host 0.0.0.0 --port 8000"]
