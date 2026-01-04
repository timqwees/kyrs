# Инструкция по установке

## Шаги для запуска проекта

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Применение миграций

```bash
cd timqwees
python manage.py makemigrations
python manage.py migrate
```

### 3. Создание суперпользователя

```bash
python manage.py createsuperuser
```

Или используйте скрипт `./run.sh` который все сделает автоматически.

## Что реализовано для оценки 5:

✅ **Django REST Framework**
- Serializers для всех моделей
- ViewSets с CRUD операциями
- Валидация полей (минимум 1 метод своей логики)

✅ **@action методы**
- `@action(methods=['GET'], detail=False)` - my_restaurants, recent_orders, popular_products
- `@action(methods=['POST'], detail=True)` - update_status, change_status, update_price

✅ **Запросы с Q**
- Минимум 2 запроса с OR, AND, NOT
- В ProductViewSet и OrderViewSet

✅ **Пагинация**
- Настроена в REST_FRAMEWORK settings (PAGE_SIZE=10)

✅ **5 вариантов фильтрации**
1. По текущему пользователю (get_queryset)
2. По именованным аргументам (?owner_id=1)
3. По GET параметрам (?name=пицца&min_price=100)
4. DjangoFilterBackend (filterset_class)
5. SearchFilter (search_fields)

✅ **Django-simple-history**
- Подключено в моделях Restaurant, Product, Order
- Middleware добавлен

✅ **Экспорт в Excel**
- ProductResource с get_export_queryset, dehydrate_formatted_price
- OrderResource с get_export_queryset, dehydrate_status_display, dehydrate_formatted_date, dehydrate_formatted_total

✅ **Management команды**
- create_sample_data - создание тестовых данных
- cleanup_old_orders - очистка старых заказов

✅ **Linter**
- Настроен .flake8

✅ **Docker**
- Dockerfile
- docker-compose.yml
- .dockerignore

## API Endpoints

- `/api/restaurants/` - список ресторанов
- `/api/products/` - список продуктов
- `/api/orders/` - список заказов
- `/api/restaurants/{id}/my_restaurants/` - рестораны пользователя
- `/api/products/popular_products/` - популярные продукты
- `/api/orders/recent_orders/` - недавние заказы
- `/api/orders/{id}/change_status/` - изменить статус заказа
