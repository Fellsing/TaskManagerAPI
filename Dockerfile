FROM python:3.14.2

WORKDIR /app

RUN pip install poetry

RUN poetry config virtualenvs.create false

COPY poetry.lock pyproject.toml* ./

RUN poetry install --no-interaction --no-ansi --only main --no-root

COPY . .

CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]