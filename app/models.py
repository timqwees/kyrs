from django.db import models
from django.contrib.auth.models import User

from simple_history.models import HistoricalRecords


class Restaurant(models.Model):
    """Модель ресторана"""
    name = models.CharField(max_length=200, verbose_name="Название", db_index=True)  # индекс для поиска
    address = models.CharField(max_length=300, verbose_name="Адрес")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Ресторан"  # Единственное число
        verbose_name_plural = "Рестораны"  # Множественное число
        ordering = ['name']  # Сортировка по умолчанию
        indexes = [
            models.Index(fields=['name'], name='restaurant_name_idx'),
            models.Index(fields=['owner', 'created_at'], name='restaurant_owner_created_idx'),
        ]

    def __str__(self):
        return self.name


class Product(models.Model):
    """Модель продукта"""
    name = models.CharField(max_length=200, verbose_name="Название", db_index=True)  # индекс
    description = models.TextField(verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, verbose_name="Ресторан")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
        ordering = ['name']
        indexes = [
            models.Index(fields=['restaurant', 'name'], name='product_restaurant_name_idx'),
            models.Index(fields=['price'], name='product_price_idx'),
        ]

    def __str__(self):
        return f"{self.name} - {self.restaurant.name}"


class Courier(models.Model):
    """Модель курьера"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    phone = models.CharField(max_length=20, verbose_name="Телефон", db_index=True)  # индекс
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Курьер"
        verbose_name_plural = "Курьеры"
        ordering = ['user__username']
        indexes = [
            models.Index(fields=['is_active'], name='courier_active_idx'),
        ]

    def __str__(self):
        return f"{self.user.username}"


class Order(models.Model):
    """Модель заказа"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('preparing', 'Готовится'),
        ('ready', 'Готов'),
        ('delivering', 'Доставляется'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Клиент")
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, verbose_name="Ресторан")
    courier = models.ForeignKey(Courier, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Курьер")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    address = models.CharField(max_length=300, verbose_name="Адрес доставки")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Общая стоимость")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status'], name='order_status_idx'),
            models.Index(fields=['customer', 'created_at'], name='order_customer_created_idx'),
            models.Index(fields=['restaurant', 'status'], name='order_restaurant_status_idx'),
        ]

    def __str__(self):
        return f"Заказ #{self.id} - {self.customer.username}"


class OrderItem(models.Model):
    """Модель элемента заказа"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Продукт")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")

    class Meta:
        verbose_name = "Элемент заказа"
        verbose_name_plural = "Элементы заказа"
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} x{self.quantity} в заказе #{self.order.id}"

    def get_total(self):
        """Возвращает общую стоимость элемента заказа"""
        return self.price * self.quantity
