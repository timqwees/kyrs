#!/bin/bash

echo "=================================="
echo "Запуск проекта доставки еды"
echo "=================================="

echo ""
echo "1. Создание миграций..."
python manage.py makemigrations

echo ""
echo "2. Применение миграций..."
python manage.py migrate --no-input

echo ""
echo "3. Проверка и создание суперпользователя..."
python manage.py shell << 'PYTHON_SCRIPT'
from django.contrib.auth import get_user_model

User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print("Создание суперпользователя...")
    username = "admin"
    email = "admin@example.com"
    password = "admin"
    try:
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"Суперпользователь создан!")
        print(f"Имя: {username}")
        print(f"Пароль: {password}")
    except Exception as e:
        print(f"Ошибка при создании суперпользователя: {e}")
else:
    print("Суперпользователь уже существует")
PYTHON_SCRIPT

echo ""
echo "4. Создание тестовых данных..."
python manage.py create_sample_data

echo ""
echo "5. Запуск сервера разработки..."
echo "=================================="
echo "Сервер будет доступен по адресу: http://localhost:8080"
echo "Админ-панель: http://localhost:8080/admin"
echo "Логин: admin"
echo "Пароль: admin"
echo "=================================="
echo ""

python manage.py runserver 0.0.0.0:8080
