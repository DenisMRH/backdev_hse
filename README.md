## Требования

- Python 3.10+
- Docker и Docker Compose
- Установленные зависимости: `pip install -r requirements.txt`

## Запуск инфраструктуры

```bash
docker-compose up -d
```

Поднимаются:

- **PostgreSQL** — порт 5434, БД `ads_db`
- **PostgreSQL (hw)** — порт 5435, БД `hw` (для проверки ДЗ и таблицы аккаунтов)
- **Redis** — порт 6379
- **Redpanda (Kafka)** — порт 9092
- **Redpanda Console** — http://localhost:8080

Перед первым запуском приложения примените миграции из папки `migrations/` по порядку: 001, 002, 003, 004, 005 (таблица `account` для авторизации).

## Запуск API

Из корня проекта:

```bash
uvicorn main:app --reload
```

API будет доступен по адресу http://127.0.0.1:8000. Документация: http://127.0.0.1:8000/docs.

## Запуск воркера

Воркер обрабатывает задачи модерации из топика Kafka `moderation`: получает сообщения, вызывает ML-модель и обновляет записи в таблице `moderation_results`. При ошибках выполняет до 3 попыток, затем отправляет сообщение в DLQ (`moderation_dlq`).

```bash
python -m app.workers.moderation_worker
```

## Тесты

```bash
pytest -m "not integration" -v
pytest -m integration -v
```
