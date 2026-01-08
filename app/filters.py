import django_filters
from .models import Product, Order, Restaurant


class ProductFilter(django_filters.FilterSet):
    """Фильтр для продуктов с использованием django_filters"""
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    restaurant_name = django_filters.CharFilter(field_name='restaurant__name', lookup_expr='icontains')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Product
        fields = ['restaurant', 'price']


class OrderFilter(django_filters.FilterSet):
    """Фильтр для заказов с использованием django_filters"""
    min_total = django_filters.NumberFilter(field_name='total_price', lookup_expr='gte')
    max_total = django_filters.NumberFilter(field_name='total_price', lookup_expr='lte')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    restaurant_name = django_filters.CharFilter(field_name='restaurant__name', lookup_expr='icontains')

    class Meta:
        model = Order
        fields = ['status', 'restaurant', 'customer', 'courier', 'total_price']


class RestaurantFilter(django_filters.FilterSet):
    """Фильтр для ресторанов с использованием django_filters"""
    owner_username = django_filters.CharFilter(field_name='owner__username', lookup_expr='icontains')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')

    class Meta:
        model = Restaurant
        fields = ['owner', 'name']
