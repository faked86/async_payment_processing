# Асинхронный сервис процессинга платежей

Микросервис для регистрации платежей, эмуляции их обработки платежным шлюзом и гарантированной доставки уведомлений (вебхуков) системам-клиентам.

## Технологический стек
* **Язык программирования:** Python 3.14
* **Веб-фреймворк:** FastAPI
* **Работа с очередями:** FastStream + RabbitMQ
* **База данных:** PostgreSQL 18 + SQLAlchemy 2.1 (asyncpg)
* **Миграции БД:** Alembic
* **Валидация и настройки:** Pydantic v2 + Pydantic Settings
* **Пакетный менеджер:** uv

---

## Архитектурная структура проекта

Проект разделен на изолированные слои для обеспечения независимости бизнес-логики от транспортных протоколов и инфраструктуры:

```text
src/
├── common/          # Общие структуры данных (DTO, типы)
├── config/          # Конфигурация окружения и синглтон брокера RabbitMQ
├── core/            # Слой бизнес-логики
├── db/              # Слой доступа к данным
├── queue/           # Инфраструктура брокера
├── server/          # Транспортный слой API
└── consumer/        # Транспортный слой очередей
```

---

## Инструкция по развертыванию и запуску

### Конфигурация окружения

Для запуска сервиса необходимо создать файл `.env` в корневом каталоге проекта со следующим содержимым:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=payment_user
DB_PASSWORD=payment_secure_password
DB_DATABASE_NAME=payment_processing

RABBIT_HOST=localhost
RABBIT_PORT=5672
RABBIT_USER=guest
RABBIT_PASSWORD=guest

API_KEY=your_secret_static_api_key
```

### Запуск через Docker Compose

Выполните команду в корневом каталоге:
```bash
docker compose up --build
```

### Автоматический жизненный цикл при старте контейнеров
1. Контейнеры `api` и `consumer` ожидают прохождения проверок готовности (`healthcheck`) со стороны сервисов `postgres` и `rabbitmq`.
2. При запуске контейнера `api` срабатывает сценарий `entrypoint.sh`, который автоматически применяет все актуальные миграции Alembic к базе данных (`alembic upgrade head`), после чего инициализирует ASGI-сервер Uvicorn.
3. В рамках старта Uvicorn активируется lifespan-контекст, открывающий асинхронное соединение с RabbitMQ для брокера и порождающий фоновую задачу Outbox Relay.
4. Контейнер `consumer` инициализирует FastStream, декларативно создает топологию очередей (`payments.new`, `payments.new.dlq`, обменник `payments.dlx`) и начинает прослушивание сообщений.

---

## Спецификация API Эндпоинтов

Документация OpenAPI (Swagger) доступна после запуска по адресу: `http://localhost:8000/docs`

### Аутентификация
Все эндпоинты защищены статическим ключом. Необходимо передавать заголовок:
`X-API-Key: <значение_из_переменной_окружения>`

### 1. Создание платежа
* **Метод и путь:** `POST /api/v1/payments`
* **Обязательный заголовок:** `Idempotency-Key: <уникальная_строка>`
* **Тело запроса (JSON):**
  ```json
  {
    "amount": 1500.50,
    "currency": "RUB",
    "description": "Оплата заказа #105",
    "metadata_dict": {"user_id": 42},
    "webhook_url": "https://client-system.com"
  }
  ```
* **Ответ (202 Accepted):**
  ```json
  {
    "id": "cd1f8c70-5cef-4f7b-b8f8-b4cfccac424b",
    "status": "pending",
    "created_at": "2026-10-04T13:11:31.861000Z"
  }
  ```

### 2. Получение статуса платежа
* **Метод и путь:** `GET /api/v1/payments/{payment_id}`
* **Ответ (200 OK):**
  ```json
  {
    "id": "cd1f8c70-5cef-4f7b-b8f8-b4cfccac424b",
    "amount": 1500.5000,
    "currency": "RUB",
    "description": "Оплата заказа #105",
    "status": "succeeded",
    "metadata_dict": {"user_id": 42},
    "idempotency_key": "unique_string_123",
    "webhook_url": "https://client-system.com",
    "created_at": "2026-10-04T13:11:31.861000Z",
    "updated_at": "2026-10-04T13:11:35.120000Z"
  }
  ```

---

## Логика отправки вебхуков (Формат уведомлений)

После обработки транзакции воркером (эмуляция шлюза: 90% успех, 10% отказ) на адрес `webhook_url` отправляется асинхронный POST-запрос со следующим JSON-телом:

```json
{
  "event": "payment.success",
  "payment_id": "cd1f8c70-5cef-4f7b-b8f8-b4cfccac424b",
  "amount": 1500.5000,
  "currency": "RUB"
}
```
