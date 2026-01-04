from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import Restaurant, Product, Order, OrderItem


class Command(BaseCommand):
    help = 'Создает тестовые данные для проекта'

    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых данных...')

        # Создание пользователя
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com'}
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Создан пользователь: {user.username}'))

        # Создание ресторана
        restaurant, created = Restaurant.objects.get_or_create(
            name='Тестовый ресторан',
            defaults={
                'address': 'ул. Тестовая, д. 1',
                'phone': '+79991234567',
                'owner': user
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Создан ресторан: {restaurant.name}'))

        # Создание продуктов
        products_data = [
            {'name': 'Пицца Маргарита', 'description': 'Классическая пицца', 'price': 500},
            {'name': 'Бургер', 'description': 'Сочный бургер', 'price': 350},
            {'name': 'Салат Цезарь', 'description': 'Свежий салат', 'price': 250},
        ]

        for prod_data in products_data:
            product, created = Product.objects.get_or_create(
                name=prod_data['name'],
                restaurant=restaurant,
                defaults=prod_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Создан продукт: {product.name}'))

        self.stdout.write(self.style.SUCCESS('Тестовые данные успешно созданы!'))
