from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal
import requests

from .models import Restaurant, Product, Order, OrderItem
from .forms import RegisterForm, LoginForm, OrderForm, ProductForm
from .tasks import send_order_confirmation_email


def index(request: HttpRequest) -> HttpResponse:
    """Главная страница со списком ресторанов"""
    restaurants = Restaurant.objects.all()
    cart_items_count = get_cart_items_count(request)

    return render(request, 'index.html', {
        'restaurants': restaurants,
        'cart_items_count': cart_items_count
    })


def restaurant_detail(request: HttpRequest, restaurant_id: int) -> HttpResponse:
    """Детальная страница ресторана с продуктами"""
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    products = Product.objects.filter(restaurant=restaurant)
    cart_items_count = get_cart_items_count(request)
    cart = request.session.get('cart', {})

    # Добавляем информацию о количестве в корзине для каждого продукта
    for product in products:
        product.in_cart = cart.get(str(product.id), 0)

    return render(request, 'restaurant.html', {
        'restaurant': restaurant,
        'products': products,
        'cart_items_count': cart_items_count
    })


@login_required
def orders(request: HttpRequest) -> HttpResponse:
    """Список заказов (клиент видит только свои, админ - все)"""
    if request.user.is_superuser or request.user.is_staff:
        orders_list = Order.objects.all()
    else:
        orders_list = Order.objects.filter(customer=request.user)

    cart_items_count = get_cart_items_count(request)
    return render(request, 'orders.html', {
        'orders': orders_list,
        'cart_items_count': cart_items_count
    })


@login_required
def order_detail(request: HttpRequest, order_id: int) -> HttpResponse:
    """Детальная страница заказа"""
    order = get_object_or_404(Order, id=order_id)

    # Проверка прав доступа
    if not (request.user.is_superuser or request.user.is_staff or order.customer == request.user):
        messages.error(request, 'У вас нет доступа к этому заказу')
        return redirect('orders')

    cart_items_count = get_cart_items_count(request)
    return render(request, 'order.html', {
        'order': order,
        'cart_items_count': cart_items_count
    })


def register(request: HttpRequest) -> HttpResponse:
    """Регистрация нового клиента => задание 4 (часть 1 method)"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('index')
    else:
        form = RegisterForm()

    cart_items_count = get_cart_items_count(request)
    return render(request, 'register.html', {
        'form': form,
        'cart_items_count': cart_items_count
    })


def login_view(request: HttpRequest) -> HttpResponse:
    """Вход в систему"""
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')
                next_url = request.GET.get('next', 'index')
                return redirect(next_url)
            else:
                messages.error(request, 'Неверное имя пользователя или пароль')
    else:
        form = LoginForm()

    cart_items_count = get_cart_items_count(request)
    return render(request, 'login.html', {
        'form': form,
        'cart_items_count': cart_items_count
    })


def logout_view(request: HttpRequest) -> HttpResponse:
    """Выход из системы"""
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'Вы вышли из системы')
    return redirect('index')


@login_required
def cart(request: HttpRequest) -> HttpResponse:
    """Корзина клиента"""
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = Decimal('0.00')

    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            item_total = product.price * quantity
            total_price += item_total
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total': item_total
            })
        except Product.DoesNotExist:
            continue

    cart_items_count = get_cart_items_count(request)
    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'cart_items_count': cart_items_count
    })


@require_POST
@login_required
def add_to_cart(request: HttpRequest, product_id: int) -> HttpResponse:
    """Добавление товара в корзину"""
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))

    cart = request.session.get('cart', {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        cart[product_id_str] += quantity
    else:
        cart[product_id_str] = quantity

    request.session['cart'] = cart
    messages.success(request, f'{product.name} добавлен в корзину')

    return redirect('restaurant_detail', restaurant_id=product.restaurant.id)


@require_POST
@login_required
def remove_from_cart(request: HttpRequest, product_id: int) -> HttpResponse:
    """Удаление товара из корзины"""
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        del cart[product_id_str]
        request.session['cart'] = cart
        messages.success(request, 'Товар удален из корзины')

    return redirect('cart')


@require_POST
@login_required
def update_cart(request: HttpRequest, product_id: int) -> HttpResponse:
    """Обновление количества товара в корзине"""
    quantity = int(request.POST.get('quantity', 1))

    cart = request.session.get('cart', {})
    product_id_str = str(product_id)

    if quantity > 0:
        cart[product_id_str] = quantity
    else:
        if product_id_str in cart:
            del cart[product_id_str]

    request.session['cart'] = cart
    return redirect('cart')


@login_required
def checkout(request: HttpRequest) -> HttpResponse:
    """Оформление заказа"""
    cart = request.session.get('cart', {})

    if not cart:
        messages.error(request, 'Ваша корзина пуста')
        return redirect('cart')

    # Проверяем, что все товары из одного ресторана
    products = Product.objects.filter(id__in=cart.keys())
    restaurants = products.values_list('restaurant', flat=True).distinct()

    if len(restaurants) > 1:
        messages.error(request, 'Все товары должны быть из одного ресторана')
        return redirect('cart')

    restaurant = Restaurant.objects.get(id=restaurants[0])

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Транзакция: все операции выполняются атомарно (либо все, либо ничего)
            try:
                with transaction.atomic():
                    # Создаем заказ
                    order = Order.objects.create(
                        customer=request.user,
                        restaurant=restaurant,
                        address=form.cleaned_data['address'],
                        status='pending'
                    )

                    # Добавляем элементы заказа
                    total_price = Decimal('0.00')
                    for product_id, quantity in cart.items():
                        product = Product.objects.select_for_update().get(id=product_id)  # блокировка строки
                        item_total = product.price * quantity
                        total_price += item_total
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=quantity,
                            price=product.price
                        )

                    order.total_price = total_price
                    order.save()

                    # Очищаем корзину
                    request.session['cart'] = {}

                # Отправка письма через Celery (асинхронно)
                send_order_confirmation_email.delay(
                    order.id,
                    request.user.email,
                    request.user.username
                )

                messages.success(request, f'Заказ #{order.id} успешно оформлен! Письмо подтверждения отправлено на {request.user.email} (проверьте Mailhog)')
                return redirect('order_detail', order_id=order.id)

            except Exception as e:
                messages.error(request, f'Ошибка при оформлении заказа: {e}')
                return redirect('cart')
    else:
        form = OrderForm()

    # Подсчитываем итоговую стоимость
    total_price = Decimal('0.00')
    cart_items = []
    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        item_total = product.price * quantity
        total_price += item_total
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'total': item_total
        })

    cart_items_count = get_cart_items_count(request)
    return render(request, 'checkout.html', {
        'form': form,
        'restaurant': restaurant,
        'cart_items': cart_items,
        'total_price': total_price,
        'cart_items_count': cart_items_count
    })


def get_cart_items_count(request: HttpRequest) -> int:
    """Получить количество товаров в корзине"""
    cart = request.session.get('cart', {})
    return sum(cart.values())


# ========================================
# CRUD операции для продуктов
# ========================================

def product_list(request: HttpRequest) -> HttpResponse:
    """Просмотр всех продуктов (READ)"""
    products = Product.objects.all().select_related('restaurant')
    cart_items_count = get_cart_items_count(request)
    return render(request, 'product_list.html', {
        'products': products,
        'cart_items_count': cart_items_count
    })


@login_required
def product_create(request: HttpRequest) -> HttpResponse:
    """Создание нового продукта (CREATE)"""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Продукт "{product.name}" успешно создан!')
            return redirect('product_list')
    else:
        form = ProductForm()

    cart_items_count = get_cart_items_count(request)
    return render(request, 'product_form.html', {
        'form': form,
        'title': 'Создать продукт',
        'cart_items_count': cart_items_count
    })


@login_required
def product_update(request: HttpRequest, product_id: int) -> HttpResponse:
    """Редактирование продукта (UPDATE)"""
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Продукт "{product.name}" успешно обновлен!')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)

    cart_items_count = get_cart_items_count(request)
    return render(request, 'product_form.html', {
        'form': form,
        'title': 'Редактировать продукт',
        'product': product,
        'cart_items_count': cart_items_count
    })


@login_required
def product_delete(request: HttpRequest, product_id: int) -> HttpResponse:
    """Удаление продукта (DELETE)"""
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Продукт "{product_name}" успешно удален!')
        return redirect('product_list')

    cart_items_count = get_cart_items_count(request)
    return render(request, 'product_delete.html', {
        'product': product,
        'cart_items_count': cart_items_count
    })


# ========================================
# Dev Tools и тестирование email
# ========================================

@login_required
def dev_tools(request: HttpRequest) -> HttpResponse:
    """Страница инструментов разработчика (OAuth2, Mailhog, Celery, Silk, API)"""
    if not request.user.is_superuser:
        messages.error(request, 'Доступ только для администратора')
        return redirect('index')
    return render(request, 'dev_tools.html')


@require_POST
@login_required
def test_email(request: HttpRequest) -> HttpResponse:
    """Тестовая отправка email через Mailhog"""
    email = request.POST.get('email', 'test@test.com')
    subject = request.POST.get('subject', 'Тестовое письмо')
    message = request.POST.get('message', 'Это тестовое письмо.')

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email='noreply@timqwees.com',
            recipient_list=[email],
            fail_silently=False,
        )
        messages.success(request, f'Письмо отправлено на {email}! Проверьте Mailhog: http://localhost:8025')
    except Exception as e:
        messages.warning(request, f'Письмо не отправлено (Mailhog не запущен?): {e}. Для теста запусти: docker-compose up mailhog')

    return redirect('dev_tools')


# ========================================
# OAuth2 — демонстрация работы протокола
# ========================================

@login_required
def oauth2_demo(request: HttpRequest) -> HttpResponse:
    """Демонстрационная страница OAuth2 — получение и использование токена"""
    from oauth2_provider.models import Application, AccessToken

    # Список всех OAuth2 приложений
    applications = Application.objects.all()
    access_tokens = AccessToken.objects.filter(user=request.user).order_by('-created')

    return render(request, 'oauth2_demo.html', {
        'applications': applications,
        'access_tokens': access_tokens,
        'base_url': request.build_absolute_uri('/'),
    })


def oauth2_callback(request: HttpRequest) -> HttpResponse:
    """Callback для OAuth2 — получает authorization code и обменивает его на access_token"""
    code = request.GET.get('code')
    error = request.GET.get('error')

    if error:
        messages.error(request, f'OAuth2 ошибка: {error}')
        return redirect('oauth2_demo')

    if not code:
        messages.error(request, 'Не получен authorization code')
        return redirect('login')

    # Обмен code на access_token через OAuth2 token endpoint
    base_url = request.build_absolute_uri('/').rstrip('/')
    token_url = f'{base_url}/api/o/token/'

    client_id = request.session.get('oauth2_client_id', '')
    client_secret = request.session.get('oauth2_client_secret', '')

    try:
        response = requests.post(token_url, data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': f'{base_url}/oauth2/callback/',
            'client_id': client_id,
            'client_secret': client_secret,
        })

        token_data = response.json()

        if 'access_token' in token_data:
            request.session['oauth2_access_token'] = token_data['access_token']
            messages.success(request, f'OAuth2 токен получен! Access token: {token_data["access_token"][:20]}...')
            return redirect('oauth2_demo')
        else:
            messages.error(request, f'Ошибка получения токена: {token_data}')
            return redirect('oauth2_demo')

    except Exception as e:
        messages.error(request, f'Ошибка при обмене кода на токен: {e}')
        return redirect('oauth2_demo')
