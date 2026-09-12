FROM python:3.13-slim
WORKDIR /app
COPY backend/pyproject.toml ./backend/pyproject.toml
COPY README.md ./README.md
COPY backend/src ./backend/src
COPY backend/migrations ./backend/migrations
COPY backend/scripts ./backend/scripts
COPY backend/config ./backend/config
COPY backend/alembic.ini ./backend/alembic.ini
RUN python -m pip install --no-cache-dir --upgrade "pip>=26.2" \
    && pip install --no-cache-dir ./backend
RUN groupadd --system projectbet && useradd --system --gid projectbet --home-dir /app projectbet \
    && chown -R projectbet:projectbet /app
USER projectbet
CMD ["sh", "-c", "alembic -c backend/alembic.ini upgrade head && uvicorn brain_projectbet.api.main:app --host 0.0.0.0 --port 8000"]
