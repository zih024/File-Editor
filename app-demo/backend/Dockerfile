FROM python:3.11-alpine

WORKDIR /app

RUN pip install --no-cache-dir poetry==2.1.1

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false

RUN poetry install --no-interaction --no-ansi --no-root

ENV PYTHONPATH=/app/src

COPY ./src /app/src

EXPOSE 8000

CMD ["fastapi", "run", "src/backend/main.py", "--port", "8000"]