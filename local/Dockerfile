FROM ghcr.io/astral-sh/uv:python3.12-bookworm

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./

RUN uv sync --locked --no-install-project --no-dev

COPY . .

RUN uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH"

COPY scripts/start.sh /app/scripts/start.sh
RUN chmod +x /app/scripts/start.sh

RUN groupadd --system app && useradd --system --gid app --create-home app && chown -R app:app /app

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1', 8000)); s.close()"

USER app

CMD ["/app/scripts/start.sh"]