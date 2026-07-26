# Локальная разработка

## Установка UV

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Установка зависимостей

```bash
# Все зависимости (включая dev)
uv sync

# Только prod зависимости
uv sync --no-dev
```

## Запуск

```bash
# Запуск приложения
uv run uvicorn src.main:main_app --host 0.0.0.0 --port 8000 --reload

# Запуск тестов
uv run pytest

# Запуск миграций
uv run alembic upgrade head

# Любая команда через uv run
uv run python -c "print('hello')"
```

## Docker

```bash
# Сборка и запуск
docker compose up -d --build

# Тестовая БД
docker compose -f docker-compose.test.yml up -d
```

## Добавление зависимости

```bash
# Prod зависимость
uv add httpx

# Dev зависимость
uv add --group dev pytest-cov
```
