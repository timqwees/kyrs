from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import timedelta

from .models import Restaurant, Product, Order, OrderItem
from .serializers import (
    RestaurantSerializer, ProductSerializer, OrderSerializer, OrderItemSerializer
) #DRF
from .filters import ProductFilter, OrderFilter, RestaurantFilter

"""API RestaurantViewSet"""
class RestaurantViewSet(viewsets.ModelViewSet):
    #ViewSet для ресторанов
    queryset = Restaurant.objects.all() #получаем все обьекты полей с Restaurant
    serializer_class = RestaurantSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RestaurantFilter
    search_fields = ['name', 'address', 'phone']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """Фильтрация по текущему пользователю (если не админ)"""
        queryset = super().get_queryset()
        user = self.request.user

        # Фильтр по именованным аргументам в URL
        owner_id = self.request.query_params.get('owner_id', None)
        if owner_id:
            queryset = queryset.filter(owner_id=owner_id)

        # Фильтр по GET параметрам
        name_filter = self.request.query_params.get('name', None)
        if name_filter:
            queryset = queryset.filter(name__icontains=name_filter)

        # Если пользователь не админ, показываем только его рестораны
        if user.is_authenticated and not user.is_superuser:
            queryset = queryset.filter(owner=user)

        return queryset.select_related('owner')

    @action(detail=True, methods=['get'])
    def my_restaurants(self, request):
        """Получить рестораны текущего пользователя"""
        if not request.user.is_authenticated:
            return Response({'error': 'Требуется авторизация'}, status=status.HTTP_401_UNAUTHORIZED)

        restaurants = Restaurant.objects.filter(owner=request.user)
        serializer = self.get_serializer(restaurants, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Обновить статус ресторана (пример POST для объекта)"""
        restaurant = self.get_object()
        # Здесь можно добавить логику обновления статуса
        return Response({'message': f'Ресторан {restaurant.name} обновлен'})


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet для продуктов"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """Фильтрация с использованием Q объектов"""
        queryset = super().get_queryset()

        # Фильтр по GET параметрам
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)

        # Использование Q для сложных запросов
        q_objects = Q()

        if min_price:
            q_objects &= Q(price__gte=min_price)
        if max_price:
            q_objects &= Q(price__lte=max_price)

        # Фильтр по диапазону цен (django_filters через Q)
        price_range = self.request.query_params.get('price_range', None)
        if price_range:
            try:
                min_p, max_p = price_range.split('-')
                q_objects &= Q(price__gte=float(min_p)) & Q(price__lte=float(max_p))
            except:
                pass

        # Фильтр по текущему пользователю (рестораны пользователя)
        user = self.request.user
        if user.is_authenticated and not user.is_superuser:
            q_objects &= Q(restaurant__owner=user)

        if q_objects:
            queryset = queryset.filter(q_objects)

        return queryset.select_related('restaurant', 'restaurant__owner')

    @action(detail=False, methods=['get'])
    def popular_products(self, request):
        """Получить популярные продукты (продукты из заказов)"""
        # Сложный запрос с Q: продукты, которые есть в заказах и не отменены
        products = Product.objects.filter(
            Q(orderitem__order__status__in=['pending', 'preparing', 'ready', 'delivering', 'completed']) &
            ~Q(orderitem__order__status='cancelled')
        ).distinct().annotate(
            total_ordered=Sum('orderitem__quantity')
        ).order_by('-total_ordered')[:10]

        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_price(self, request, pk=None):
        """Обновить цену продукта"""
        product = self.get_object()
        new_price = request.data.get('price', None)

        if new_price is None:
            return Response({'error': 'Не указана цена'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_price = float(new_price)
            if new_price <= 0:
                return Response({'error': 'Цена должна быть положительной'}, status=status.HTTP_400_BAD_REQUEST)

            product.price = new_price
            product.save()

            serializer = self.get_serializer(product)
            return Response(serializer.data)
        except ValueError:
            return Response({'error': 'Неверный формат цены'}, status=status.HTTP_400_BAD_REQUEST)


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet для заказов"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = OrderFilter
    search_fields = ['address', 'customer__username', 'restaurant__name']
    ordering_fields = ['created_at', 'total_price', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """Фильтрация с использованием Q объектов (OR, AND, NOT)"""
        queryset = super().get_queryset()
        user = self.request.user

        # Сложный запрос с Q: OR, AND, NOT
        q_objects = Q()

        # Фильтр по статусу (GET параметры)
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            q_objects &= Q(status=status_filter)

        # Фильтр по диапазону дат (GET параметры)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        if date_from:
            q_objects &= Q(created_at__gte=date_from)
        if date_to:
            q_objects &= Q(created_at__lte=date_to)

        # Фильтр по текущему пользователю
        if user.is_authenticated and not user.is_superuser:
            # Клиент видит только свои заказы
            q_objects &= Q(customer=user)

        # Сложный запрос: заказы с высоким приоритетом (большая сумма) ИЛИ не завершенные
        high_priority = self.request.query_params.get('high_priority', None)
        if high_priority == 'true':
            q_objects |= Q(total_price__gte=1000) | ~Q(status__in=['completed', 'cancelled'])

        # Еще один сложный запрос: заказы, которые НЕ отменены И (готовятся ИЛИ доставляются)
        active_orders = self.request.query_params.get('active', None)
        if active_orders == 'true':
            q_objects &= ~Q(status='cancelled') & (Q(status='preparing') | Q(status='delivering'))

        if q_objects:
            queryset = queryset.filter(q_objects)

        return queryset.select_related('customer', 'restaurant', 'courier', 'courier__user').prefetch_related('items', 'items__product')

    @action(detail=False, methods=['get'])
    def recent_orders(self, request):
        """Получить недавние заказы (за последние 7 дней)"""
        seven_days_ago = timezone.now() - timedelta(days=7)

        # Сложный запрос с Q: заказы за последние 7 дней И не отменены
        orders = Order.objects.filter(
            Q(created_at__gte=seven_days_ago) & ~Q(status='cancelled')
        ).order_by('-created_at')

        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Изменить статус заказа"""
        order = self.get_object()
        new_status = request.data.get('status', None)

        if new_status is None:
            return Response({'error': 'Не указан статус'}, status=status.HTTP_400_BAD_REQUEST)

        if new_status not in [choice[0] for choice in Order.STATUS_CHOICES]:
            return Response({'error': 'Недопустимый статус'}, status=status.HTTP_400_BAD_REQUEST)

        order.status = new_status
        order.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """Получить заказы текущего пользователя"""
        if not request.user.is_authenticated:
            return Response({'error': 'Требуется авторизация'}, status=status.HTTP_401_UNAUTHORIZED)

        orders = Order.objects.filter(customer=request.user)
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)
