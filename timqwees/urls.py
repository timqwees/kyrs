"""
URL configuration for timqwees project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter
from app import views
from app.viewsets import RestaurantViewSet, ProductViewSet, OrderViewSet

# регистрация маршрутов для viewSet
router = DefaultRouter()  # чтобы интерфейс был не используем simplerouter
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
    path('silk/', include('silk.urls', namespace='silk')),  # Django Silk — профилирование
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    # OAuth2 endpoints
    path('api/o/', RedirectView.as_view(url='/api/o/authorize/'), name='oauth2_root'),  # редирект с корня OAuth2
    path('api/o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('restaurant/<int:restaurant_id>/', views.restaurant_detail, name='restaurant_detail'),

    # Авторизация
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('accounts/', include('allauth.urls')),  # django-allauth (Google, VK)

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

    # Dev Tools и тестирование
    path('dev-tools/', views.dev_tools, name='dev_tools'),
    path('test-email/', views.test_email, name='test_email'),

    # OAuth2 демо
    path('oauth2/', views.oauth2_demo, name='oauth2_demo'),
    path('oauth2/callback/', views.oauth2_callback, name='oauth2_callback'),
]
