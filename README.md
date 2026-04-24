### Task Manager API
RESTful API для управления задачами с интеграцией Telegram-бота и системой умных уведомлений. Проект построен на современном стеке Python с акцентом на асинхронность, безопасность.

#### Стек технологий
*   **Framework:** FastAPI 
*   **Database:** PostgreSQL (с асинхронным драйвером asyncpg), SQLite (с асинхронным драйвером aiosqlite) - для тестов
*   **ORM:** SQLAlchemy 2.0 
*   **Migrations:** Alembic 
*   **Validation:** Pydantic v2
*   **Security:** JWT (Access + Refresh tokens), Argon2
*   **Caching & Queues:** Redis & Celery
*   **Dependency Management:** Poetry
*   **Containerization:** Docker & Docker Compose 
*   **CI/CD:** GitHub Actions

#### Основные возможности
*   Система аутентификации и авторизации пользователей на базе JWT с поддержкой **Refresh-токенов** и их ротацией в Redis.
*   Интеграция с **Telegram-ботом**: привязка аккаунта и создание задач с выбором даты через встроенный календарь.
*   **Умная маршрутизация уведомлений**: автоматический выбор между Server-Sent Events (SSE) и Email в зависимости от типа события.
*   Фоновые задачи через **Celery** для обработки тяжелых операций.
*   Асинхронное взаимодействие с базой данных и использование кастомных исключений для единообразных ответов API.
*   Защита от атак по времени (timing attacks) при проверке паролей с использованием `DUMMY_HASH`.
*   Мониторинг производительности через middleware и автоматическое тестирование (Pytest) в CI/CD пайплайне.

#### Установка и запуск
##### Требования
*   Docker
*   Docker Compose

##### Запуск приложения
1.  Клонируйте репозиторий:
    ```bash
    git clone https://github.com/Fellsing/TaskManagerAPI.git
    ```
2.  Создайте файл `.env` на основе примера `.env.example`.
3.  Запустите проект через Docker Compose:
    ```bash
    docker-compose up --build
    ```
4.  **Примечание по безопасности**: В учебных целях в коде оставлены дефолтные значения секретных ключей, что позволяет запустить проект без настройки переменных окружения.

##### Управление базой данных
*   Миграции применяются автоматически при старте контейнера. Если необходимо выполнить команды Alembic вручную:
*   Применить миграции: `docker-compose exec app alembic upgrade head`
*   Создать новую миграцию: `docker-compose exec app alembic revision --autogenerate -m "описание"`


