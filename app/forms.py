from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Product


class RegisterForm(UserCreationForm):
    """Форма регистрации клиента"""
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(max_length=30, required=False, label="Имя")
    last_name = forms.CharField(max_length=30, required=False, label="Фамилия")

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Имя пользователя"
        self.fields['password1'].label = "Пароль"
        self.fields['password2'].label = "Подтверждение пароля"


class LoginForm(forms.Form):
    """Форма входа"""
    username = forms.CharField(label="Имя пользователя")
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")


class CustomAuthenticationForm(AuthenticationForm):
    """Кастомная форма аутентификации для админ-панели Unfold"""
    username = forms.CharField(
        label="Имя пользователя",
        widget=forms.TextInput(attrs={
            'class': 'form-input block w-full mt-1',
            'placeholder': 'Введите имя пользователя',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input block w-full mt-1',
            'placeholder': 'Введите пароль'
        })
    )


class OrderForm(forms.Form):
    """Форма оформления заказа"""
    address = forms.CharField(
        max_length=300,
        label="Адрес доставки",
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Введите полный адрес доставки'})
    )


class ProductForm(forms.ModelForm):
    """Форма для создания и редактирования продукта"""
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'restaurant']
        labels = {
            'name': 'Название',
            'description': 'Описание',
            'price': 'Цена',
            'restaurant': 'Ресторан'
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-input'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-input'}),
            'restaurant': forms.Select(attrs={'class': 'form-input'})
        }
