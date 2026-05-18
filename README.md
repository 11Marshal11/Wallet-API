# Wallet API

Async REST-сервис для управления балансами кошельков. FastAPI + PostgreSQL + SQLAlchemy 2 (async) + Alembic.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/wallets/{wallet_uuid}/operation` | Изменение баланса (`DEPOSIT` / `WITHDRAW`) |
| `GET`  | `/api/v1/wallets/{wallet_uuid}` | Получить текущий баланс |
| `GET`  | `/health` | Health-check |

### Пример запроса

```bash
curl -X POST http://localhost:8000/api/v1/wallets/6f6f6f6f-6f6f-6f6f-6f6f-6f6f6f6f6f6f/operation \
  -H 'Content-Type: application/json' \
  -d '{"operation_type": "DEPOSIT", "amount": 1000}'
```

### Поведение

- `amount` — целое число в минимальных единицах (копейки/центы), строго > 0.
- `DEPOSIT` автоматически создаёт кошелёк, если его ещё нет (идемпотентный get-or-create по UUID).
- `WITHDRAW` для несуществующего кошелька → `404`.
- `WITHDRAW` при недостатке средств → `400`.
- `GET` несуществующего кошелька → `404`.

## Конкурентность

Списания и пополнения сериализуются через `SELECT … FOR UPDATE` внутри транзакции (см. [app/services.py](app/services.py)). При параллельных операциях над одним кошельком ни одна запись не теряется и баланс не уходит в минус. Дополнительно стоит check-constraint `balance >= 0` на уровне БД как страховка.

## Запуск

```bash
cp .env.example .env
docker compose up --build
```

Сервис — на `http://localhost:8000`, Swagger UI — `http://localhost:8000/docs`. Миграции применяются автоматически при старте контейнера `app`.

## Тесты

13 тестов pytest на реальном PostgreSQL.

```bash
# создать тестовую БД (один раз)
docker compose exec db psql -U wallet -d wallet -c "CREATE DATABASE wallet_test;"

# прогнать тесты
docker compose run --rm \
  -e DATABASE_URL=postgresql+asyncpg://wallet:wallet@db:5432/wallet_test \
  app pytest -v
```

Покрытие:
- эндпоинты (GET / DEPOSIT / WITHDRAW),
- валидация (отрицательный amount, неизвестный operation_type, кривой UUID),
- 404/400/422,
- **конкурентность**: 50 параллельных DEPOSIT (баланс точен), 50 параллельных WITHDRAW (баланс не уходит в минус, число отказов корректно), mixed deposit/withdraw.

## Структура

```
app/
  config.py          # настройки из ENV
  database.py        # async engine, session
  models.py          # SQLAlchemy модели
  schemas.py         # Pydantic схемы
  services.py        # бизнес-логика с row-level locking
  exceptions.py      # доменные исключения
  routers/wallets.py # HTTP-эндпоинты
  main.py            # FastAPI app factory
alembic/             # миграции
tests/               # pytest + httpx
Dockerfile
docker-compose.yml
```

## Стек

- Python 3.12, FastAPI, Uvicorn
- SQLAlchemy 2.0 (async, `asyncpg`)
- Alembic
- PostgreSQL 16
- pytest, pytest-asyncio, httpx
- PEP8 / ruff
