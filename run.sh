#!/bin/bash

echo "=================================="
echo "Запуск проекта доставки еды"
echo "=================================="

# Проверка наличия виртуального окружения (опционально)
if [ -d "venv" ]; then
    echo "Активация виртуального окружения..."
    source venv/bin/activate
fi

echo ""
echo "1. Создание миграций..."
python manage.py makemigrations

echo ""
echo "2. Применение миграций..."
python manage.py migrate

echo ""
echo "3. Проверка и создание суперпользователя..."
python manage.py shell << 'PYTHON_SCRIPT'
from django.contrib.auth.models import User

# Проверяем, есть ли уже суперпользователь
if not User.objects.filter(is_superuser=True).exists():
    print("Создание суперпользователя...")
    username = "admin"
    email = "admin@example.com"
    password = "admin"

    try:
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"✓ Суперпользователь создан!")
        print(f"  Имя: {username}")
        print(f"  Пароль: {password}")
    except Exception as e:
        print(f"Ошибка при создании суперпользователя: {e}")
else:
    print("✓ Суперпользователь уже существует")
PYTHON_SCRIPT

echo ""
echo "4. Запуск сервера разработки..."
echo "=================================="
echo "Сервер будет доступен по адресу: http://127.0.0.1:8000"
echo "Админ-панель: http://127.0.0.1:8000/admin"
echo "Логин: admin"
echo "Пароль: admin"
echo "=================================="
echo ""

python manage.py runserver
