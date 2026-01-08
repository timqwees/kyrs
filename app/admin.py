from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field
from datetime import datetime, timedelta
from .models import Restaurant, Product, Courier, Order, OrderItem
from django.db.models import Q


# Callback функции для Unfold
def dashboard_callback(request):
    from django.contrib.contenttypes.models import ContentType
    from .models import Order, Product, Restaurant, Courier

    return {
        "orders_count": Order.objects.count(),
        "products_count": Product.objects.count(),
        "restaurants_count": Restaurant.objects.count(),
        "couriers_count": Courier.objects.count(),
    }

def command_search_callback(request, queryset, term):
    """Callback для поиска в командах (например, в ModelAdmin с Unfold)"""
    if not term or not term.strip():
        return queryset

    return queryset.filter(
        Q(name__icontains=term) |
        Q(description__icontains=term)
    )


class OrderItemInline(admin.TabularInline):
    """Инлайн для элементов заказа"""
    model = OrderItem
    extra = 1
    fields = ('product', 'quantity', 'price')
    raw_id_fields = ('product',)


# Ресурсы для экспорта
class ProductResource(resources.ModelResource):
    """Ресурс для экспорта продуктов"""
    restaurant_name = Field(attribute='restaurant__name', column_name='Ресторан')
    formatted_price = Field(column_name='Цена (форматированная)')

    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'price', 'restaurant_name', 'created_at')
        export_order = ('id', 'name', 'description', 'restaurant_name', 'price', 'formatted_price', 'created_at')

    def dehydrate_formatted_price(self, product):
        """Форматирование цены"""
        return f"{product.price} ₽"

    def get_export_queryset(self):
        """Экспорт только продуктов с ценой выше 100"""
        return Product.objects.filter(price__gte=100)


class OrderResource(resources.ModelResource):
    """Ресурс для экспорта заказов"""
    customer_name = Field(attribute='customer__username', column_name='Клиент')
    restaurant_name = Field(attribute='restaurant__name', column_name='Ресторан')
    status_display = Field(column_name='Статус (текст)')
    formatted_date = Field(column_name='Дата создания (формат)')
    formatted_total = Field(column_name='Сумма (форматированная)')

    class Meta:
        model = Order
        fields = ('id', 'customer_name', 'restaurant_name', 'status', 'status_display',
                  'address', 'total_price', 'formatted_total', 'created_at', 'formatted_date')
        export_order = ('id', 'customer_name', 'restaurant_name', 'status', 'status_display',
                       'address', 'total_price', 'formatted_total', 'created_at', 'formatted_date')

    def dehydrate_status_display(self, order):
        """Преобразование статуса в читабельный формат"""
        status_map = {
            'pending': 'Ожидает',
            'preparing': 'Готовится',
            'ready': 'Готов',
            'delivering': 'Доставляется',
            'completed': 'Завершен',
            'cancelled': 'Отменен'
        }
        return status_map.get(order.status, order.status)

    def dehydrate_formatted_date(self, order):
        """Форматирование даты в DD-MM-YYYY"""
        return order.created_at.strftime('%d-%m-%Y')

    def dehydrate_formatted_total(self, order):
        """Форматирование суммы"""
        return f"{order.total_price} ₽"

    def get_export_queryset(self):
        """Экспорт только завершенных заказов за последний месяц"""
        month_ago = datetime.now() - timedelta(days=30)
        return Order.objects.filter(
            status='completed',
            created_at__gte=month_ago
        )

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    """Админ-панель для ресторанов"""
    list_display = ('name', 'address', 'phone', 'owner', 'get_product_count', 'created_at')
    list_filter = ('created_at', 'owner')
    search_fields = ('name', 'address', 'phone')
    list_display_links = ('name',)
    raw_id_fields = ('owner',)
    date_hierarchy = 'created_at'

    @admin.display(description='Количество продуктов')
    def get_product_count(self, obj):
        return obj.product_set.count()
    get_product_count.short_description = 'Продуктов'


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    """Админ-панель для продуктов"""
    resource_class = ProductResource
    list_display = ('name', 'restaurant', 'price', 'get_order_count', 'created_at')
    list_filter = ('restaurant', 'created_at', 'price')
    search_fields = ('name', 'description')
    list_display_links = ('name',)
    raw_id_fields = ('restaurant',)
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'restaurant', 'description')
        }),
        ('Цена', {
            'fields': ('price',)
        }),
        ('Дата', {
            'fields': ('created_at',)
        }),
    )

    @admin.display(description='В заказах')
    def get_order_count(self, obj):
        return obj.orderitem_set.count()
    get_order_count.short_description = 'Заказов'


@admin.register(Courier)
class CourierAdmin(admin.ModelAdmin):
    """Админ-панель для курьеров"""
    list_display = ('user', 'phone', 'is_active', 'get_order_count')
    list_filter = ('is_active',)
    search_fields = ('user__username', 'user__email', 'phone')
    list_display_links = ('user',)
    raw_id_fields = ('user',)
    readonly_fields = ('get_order_count',)

    @admin.display(description='Активных заказов')
    def get_order_count(self, obj):
        return obj.order_set.filter(status__in=['preparing', 'ready', 'delivering']).count()
    get_order_count.short_description = 'Активных заказов'


@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin):
    """Админ-панель для заказов"""
    resource_class = OrderResource
    list_display = ('id', 'customer', 'restaurant', 'courier', 'status', 'total_price', 'get_item_count', 'created_at')
    list_filter = ('status', 'created_at', 'restaurant', 'courier')
    search_fields = ('customer__username', 'address', 'id')
    list_display_links = ('id',)
    raw_id_fields = ('customer', 'restaurant', 'courier')
    readonly_fields = ('created_at', 'updated_at', 'total_price')
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    filter_horizontal = ()
    fieldsets = (
        ('Основная информация', {
            'fields': ('customer', 'restaurant', 'courier', 'status')
        }),
        ('Доставка', {
            'fields': ('address',)
        }),
        ('Финансы', {
            'fields': ('total_price',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    @admin.display(description='Позиций')
    def get_item_count(self, obj):
        return obj.items.count()
    get_item_count.short_description = 'Позиций в заказе'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Админ-панель для элементов заказа"""
    list_display = ('id', 'order', 'product', 'quantity', 'price', 'get_total')
    list_filter = ('order__status', 'order__restaurant')
    search_fields = ('order__id', 'product__name')
    list_display_links = ('id',)
    raw_id_fields = ('order', 'product')
    readonly_fields = ('get_total',)

    @admin.display(description='Итого')
    def get_total(self, obj):
        return obj.price * obj.quantity
    get_total.short_description = 'Сумма'
