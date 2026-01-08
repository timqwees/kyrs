from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import Restaurant, Product, Order, OrderItem, Courier
from decimal import Decimal


class Command(BaseCommand):
    help = 'Создает тестовые данные для проекта'

    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых данных...')

        # Создание администратора
        admin_user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'admin@admin.com', 'is_staff': True, 'is_superuser': True}
        )
        if created:
            admin_user.set_password('testpass123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Создан администратор: {admin_user.username}'))

        # Создание курьера
        courier_user, created = User.objects.get_or_create(
            username='courier',
            defaults={'email': 'courier@courier.com'}
        )
        if created:
            courier_user.set_password('courierpass123')
            courier_user.save()
            self.stdout.write(self.style.SUCCESS(f'Создан пользователь-курьер: {courier_user.username}'))

        courier, created = Courier.objects.get_or_create(
            user=courier_user,
            defaults={'phone': '+79997654321', 'is_active': True}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Создан курьер: {courier.user.username}'))

        # Создание клиента
        customer, created = User.objects.get_or_create(
            username='customer',
            defaults={'email': 'customer@customer.com'}
        )
        if created:
            customer.set_password('customerpass123')
            customer.save()
            self.stdout.write(self.style.SUCCESS(f'Создан клиент: {customer.username}'))

        # Создание ресторана
        restaurant, created = Restaurant.objects.get_or_create(
            name='Тестовый ресторан',
            defaults={
                'address': 'ул. Тестовая, д. 1',
                'phone': '+79991234567',
                'owner': admin_user
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Создан ресторан: {restaurant.name}'))

        # Создание продуктов
        products_data = [
            {'name': 'Пицца Маргарита', 'description': 'Классическая пицца с томатным соусом и сыром', 'price': Decimal('500.00')},
            {'name': 'Бургер', 'description': 'Сочный бургер с говядиной и овощами', 'price': Decimal('350.00')},
            {'name': 'Салат Цезарь', 'description': 'Свежий салат с курицей и соусом Цезарь', 'price': Decimal('250.00')},
            {'name': 'Картошка фри', 'description': 'Хрустящая картошка фри', 'price': Decimal('150.00')},
            {'name': 'Кола', 'description': 'Газированный напиток', 'price': Decimal('100.00')},
        ]

        created_products = []
        for prod_data in products_data:
            product, created = Product.objects.get_or_create(
                name=prod_data['name'],
                restaurant=restaurant,
                defaults=prod_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Создан продукт: {product.name}'))
                created_products.append(product)
            else:
                created_products.append(product)

        # Создание заказов для клиента
        orders_data = [
            {
                'address': 'ул. Ленина, д. 10, кв. 5',
                'status': 'completed',
                'items': [
                    {'product': created_products[0], 'quantity': 2, 'price': Decimal('500.00')},  # Пицца
                    {'product': created_products[4], 'quantity': 1, 'price': Decimal('100.00')},  # Кола
                ]
            },
            {
                'address': 'пр. Победы, д. 25, кв. 12',
                'status': 'delivering',
                'items': [
                    {'product': created_products[1], 'quantity': 1, 'price': Decimal('350.00')},  # Бургер
                    {'product': created_products[3], 'quantity': 2, 'price': Decimal('150.00')},  # Картошка
                ]
            },
            {
                'address': 'ул. Советская, д. 8, кв. 3',
                'status': 'pending',
                'items': [
                    {'product': created_products[2], 'quantity': 1, 'price': Decimal('250.00')},  # Салат
                    {'product': created_products[1], 'quantity': 1, 'price': Decimal('350.00')},  # Бургер
                ]
            },
        ]

        for order_data in orders_data:
            # Создаем заказ
            order = Order.objects.create(
                customer=customer,
                restaurant=restaurant,
                courier=courier if order_data['status'] != 'pending' else None,
                status=order_data['status'],
                address=order_data['address'],
                total_price=Decimal('0.00')
            )

            # Добавляем элементы заказа
            total_price = Decimal('0.00')
            for item_data in order_data['items']:
                item_total = item_data['price'] * item_data['quantity']
                total_price += item_total

                OrderItem.objects.create(
                    order=order,
                    product=item_data['product'],
                    quantity=item_data['quantity'],
                    price=item_data['price']
                )

            # Обновляем общую стоимость заказа
            order.total_price = total_price
            order.save()

            self.stdout.write(self.style.SUCCESS(f'Создан заказ #{order.id} ({order.get_status_display()})'))

        self.stdout.write(self.style.SUCCESS('Тестовые данные успешно созданы!'))
        self.stdout.write(self.style.SUCCESS('Пользователи:'))
        self.stdout.write(self.style.SUCCESS('  Администратор: testuser / testpass123'))
        self.stdout.write(self.style.SUCCESS('  Клиент: customer / customerpass123'))
        self.stdout.write(self.style.SUCCESS('  Курьер: courier / courierpass123'))
