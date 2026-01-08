"""
URL configuration for timqwees project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.i18n import set_language as django_set_language
from rest_framework.routers import DefaultRouter
from app import views
from app.viewsets import RestaurantViewSet, ProductViewSet, OrderViewSet

# регистрация маршрутов для viewSet
router = DefaultRouter()#чтобы интерфейс был не используем simplerouter
"""Короче принцип таков:
маршрутизатор берет viewset функцию и регистрирует его в urls.py
это значит что мы регистрируем viewset функцию RestaurantViewSet и даем ей имя restaurant
и basename='restaurant' это имя которое будет использоваться в urls.py,а если не поставим basename то
имя в queryset нужно писать в функции чтобы не было page undefined тип чтобы параметр маршрута о понимал.
"""
router.register(r'restaurants', RestaurantViewSet, basename='restaurant')
"""
в RestaurantViewSet у нас маршруты создается через def автоматически регистрировать отдельно не нужно
а для method запросов GET/POST/UPDATE/HEAD... нужно использовать декоратор @action
с detail (списоком все или не списком) и методом + маршрут сам регистрируется указаф
функцию после него def имя функции = маршрут
"""
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('restaurant/<int:restaurant_id>/', views.restaurant_detail, name='restaurant_detail'),

    # Авторизация
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Смена языка
    path('i18n/setlang/', django_set_language, name='set_language'),

    # Корзина и заказы
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('checkout/', views.checkout, name='checkout'),

    # Заказы
    path('orders/', views.orders, name='orders'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),

    # CRUD для продуктов
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:product_id>/edit/', views.product_update, name='product_update'),
    path('products/<int:product_id>/delete/', views.product_delete, name='product_delete'),
]
