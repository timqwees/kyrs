FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY timqwees/ .

# Создание директории для статики
RUN mkdir -p /app/static

# Запуск миграций и сервера
CMD python manage.py migrate && python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:8000
