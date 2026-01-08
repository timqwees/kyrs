from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from decimal import Decimal

from .models import Restaurant, Product, Order, OrderItem
from .forms import RegisterForm, LoginForm, OrderForm, ProductForm


def index(request):
    """Главная страница со списком ресторанов"""
    restaurants = Restaurant.objects.all()
    cart_items_count = get_cart_items_count(request)

    # Отладочный вывод
    print(f"DEBUG: Found {restaurants.count()} restaurants")
    for restaurant in restaurants:
        print(f"DEBUG: Restaurant - ID: {restaurant.id}, Name: {restaurant.name}")

    return render(request, 'index.html', {
        'restaurants': restaurants,
        'cart_items_count': cart_items_count
    })


def restaurant_detail(request, restaurant_id):
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
def orders(request):
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
def order_detail(request, order_id):
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


def register(request):
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


def login_view(request):
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


def logout_view(request):
    """Выход из системы"""
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'Вы вышли из системы')
    return redirect('index')


@login_required
def cart(request):
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
def add_to_cart(request, product_id):
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
def remove_from_cart(request, product_id):
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
def update_cart(request, product_id):
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
def checkout(request):
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
                product = Product.objects.get(id=product_id)
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

            messages.success(request, f'Заказ #{order.id} успешно оформлен!')
            return redirect('order_detail', order_id=order.id)
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


def get_cart_items_count(request):
    """Получить количество товаров в корзине"""
    cart = request.session.get('cart', {})
    return sum(cart.values())


# ========================================
# CRUD операции для продуктов
# ========================================

def product_list(request):
    """Просмотр всех продуктов (READ)"""
    products = Product.objects.all().select_related('restaurant')
    cart_items_count = get_cart_items_count(request)
    return render(request, 'product_list.html', {
        'products': products,
        'cart_items_count': cart_items_count
    })


@login_required
def product_create(request):
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
def product_update(request, product_id):
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
def product_delete(request, product_id):
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
