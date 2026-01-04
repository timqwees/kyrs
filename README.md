# Проект доставки еды

Проект для курсовой работы с Django REST Framework.

## Установка и запуск

### Локальный запуск

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Выполните миграции:
```bash
cd timqwees
python manage.py makemigrations
python manage.py migrate
```

3. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

4. Запустите сервер:
```bash
python manage.py runserver
```

Или используйте скрипт:
```bash
./run.sh
```

### Запуск в Docker

```bash
docker-compose up --build
```

## API Endpoints

REST API доступен по адресу `/api/`:

- `/api/restaurants/` - Рестораны
- `/api/products/` - Продукты
- `/api/orders/` - Заказы

### Примеры использования API

#### Фильтрация продуктов по цене:
```
GET /api/products/?min_price=100&max_price=500
```

#### Фильтрация заказов по статусу:
```
GET /api/orders/?status=completed
```

#### Получение заказов текущего пользователя:
```
GET /api/orders/my_orders/
```

#### Изменение статуса заказа:
```
POST /api/orders/{id}/change_status/
{
    "status": "completed"
}
```

## Management команды

### Создание тестовых данных:
```bash
python manage.py create_sample_data
```

### Очистка старых заказов:
```bash
python manage.py cleanup_old_orders --days=90
```

## Фильтрация

Реализовано 5 вариантов фильтрации:

1. **Фильтр по текущему аутентифицированному пользователю** - автоматически в get_queryset
2. **Фильтр по именованным аргументам в URL** - например, `?owner_id=1`
3. **Фильтр по GET параметрам** - например, `?name=пицца&min_price=100`
4. **DjangoFilterBackend** - через filterset_class
5. **SearchFilter** - поиск по полям

## Валидация

Реализована валидация в serializers:
- Уникальность названия ресторана
- Валидация телефона
- Проверка цены (положительная, не более 100000)
- Уникальность названия продукта в ресторане
- Проверка адреса (минимум 10 символов)

## Запросы с Q

Используются сложные запросы с Q объектами (OR, AND, NOT):
- В ProductViewSet.get_queryset()
- В OrderViewSet.get_queryset()
- В @action методах

## Экспорт в Excel

Экспорт доступен в админ-панели для:
- Продуктов (только с ценой >= 100)
- Заказов (только завершенные за последний месяц)

Кастомизированы методы:
- `get_export_queryset`
- `dehydrate_*` для форматирования полей

## Linter

Настроен flake8 в файле `.flake8`

Запуск:
```bash
flake8 timqwees/
```

## Docker

Проект настроен для запуска в Docker:
- `Dockerfile` - образ приложения
- `docker-compose.yml` - оркестрация
- `.dockerignore` - исключения
