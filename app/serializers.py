from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Restaurant, Product, Order, OrderItem, Courier


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя"""
    class Meta:
        model = User
        # возвращяемые поля
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class RestaurantSerializer(serializers.ModelSerializer):
    """Сериализатор для ресторана"""
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'address', 'phone', 'owner', 'owner_username', 'created_at']
        read_only_fields = ['created_at']

    def validate_name(self, value):
        """Валидация: название ресторана должно быть уникальным"""
        if self.instance and self.instance.name == value:
            return value
        if Restaurant.objects.filter(name=value).exists():
            raise serializers.ValidationError("Ресторан с таким названием уже существует")
        return value

    def validate_phone(self, value):
        """Валидация: телефон должен содержать только цифры"""
        if not value.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise serializers.ValidationError("Телефон должен содержать только цифры и допустимые символы")
        return value


class ProductSerializer(serializers.ModelSerializer):
    """Сериализатор для продукта"""
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'restaurant', 'restaurant_name', 'created_at']
        read_only_fields = ['created_at']

    def validate_price(self, value):
        """Валидация: цена должна быть положительной"""
        if value <= 0:
            raise serializers.ValidationError("Цена должна быть больше нуля")
        if value > 100000:
            raise serializers.ValidationError("Цена не может превышать 100000")
        return value

    def validate_name(self, value):
        """Валидация: название продукта должно быть уникальным в рамках ресторана"""
        restaurant = self.initial_data.get('restaurant')
        if restaurant:
            if self.instance and self.instance.restaurant_id == restaurant and self.instance.name == value:
                return value
            if Product.objects.filter(restaurant_id=restaurant, name=value).exists():
                raise serializers.ValidationError("Продукт с таким названием уже существует в этом ресторане")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    """Сериализатор для элемента заказа"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product', 'product_name', 'quantity', 'price', 'total']

    def get_total(self, obj):
        """Вычисление общей стоимости элемента"""
        return obj.get_total()

    def validate_quantity(self, value):
        """Валидация: количество должно быть положительным"""
        if value <= 0:
            raise serializers.ValidationError("Количество должно быть больше нуля")
        if value > 100:
            raise serializers.ValidationError("Количество не может превышать 100")
        return value


class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор для заказа"""
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    courier_username = serializers.CharField(source='courier.user.username', read_only=True, allow_null=True)
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'customer_username', 'restaurant', 'restaurant_name',
            'courier', 'courier_username', 'status', 'status_display', 'address',
            'total_price', 'created_at', 'updated_at', 'items'
        ]
        read_only_fields = ['total_price', 'created_at', 'updated_at']

    def validate_address(self, value):
        """Валидация: адрес не должен быть пустым"""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Адрес должен содержать минимум 10 символов")
        return value

    def validate(self, data):
        """Валидация: проверка общей логики заказа"""
        if 'status' in data:
            status = data['status']
            if status not in [choice[0] for choice in Order.STATUS_CHOICES]:
                raise serializers.ValidationError({"status": "Недопустимый статус заказа"})
        return data


class CourierSerializer(serializers.ModelSerializer):
    """Сериализатор для курьера"""
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Courier
        fields = ['id', 'user', 'user_username', 'phone', 'is_active']
