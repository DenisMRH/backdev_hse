# Сервис модерации объявлений

FastAPI-приложение с асинхронной модерацией через Kafka: предсказание ML-модели выполняется фоновым воркером, результаты сохраняются в PostgreSQL.

## Требования

- Python 3.10+
- Docker и Docker Compose (для PostgreSQL и Redpanda/Kafka)
- Установленные зависимости: `pip install -r requirements.txt`

## Запуск инфраструктуры

```bash
docker-compose up -d
```

Поднимаются:

- **PostgreSQL** — порт 5434, БД `ads_db`
- **Redpanda (Kafka)** — порт 9092
- **Redpanda Console** — http://localhost:8080

Перед первым запуском приложения примените миграции из папки `migrations/` (например, выполните `001_initial.sql` и `002_moderation_results.sql` вручную или через ваш инструмент миграций).

## Переменные окружения

Опционально. В коде заданы значения по умолчанию, подходящие для локального запуска с Docker (порт 5434 для БД, 9092 для Kafka). При необходимости задайте переменные в окружении или в файле `.env`.

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5434/ads_db` | Подключение к PostgreSQL |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Адрес брокера Kafka (Redpanda) |

## Запуск API

Из корня проекта:

```bash
uvicorn main:app --reload
```

API будет доступен по адресу http://127.0.0.1:8000. Документация: http://127.0.0.1:8000/docs.

## Запуск воркера

Воркер обрабатывает задачи модерации из топика Kafka `moderation`: получает сообщения, вызывает ML-модель и обновляет записи в таблице `moderation_results`. При ошибках выполняет до 3 попыток, затем отправляет сообщение в DLQ (`moderation_dlq`).

**Запуск из корня проекта в отдельном терминале:**

```bash
python -m app.workers.moderation_worker
```

Убедитесь, что:

1. Запущены Docker-сервисы (`docker-compose up -d`), в том числе Redpanda и PostgreSQL.
2. Миграции применены (есть таблицы `advertisements`, `moderation_results` и т.д.).
3. Переменные окружения при необходимости заданы (или используются значения по умолчанию: `DATABASE_URL`, `KAFKA_BOOTSTRAP_SERVERS`).

Воркер подписывается на топик `moderation`, при появлении сообщений обрабатывает их и пишет результат в БД. Остановка — `Ctrl+C`.

## Тесты

```bash
pytest test_main.py -v
```
