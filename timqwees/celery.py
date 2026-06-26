"""Celery конфигурация для проекта timqwees"""
import os
from celery import Celery

# Указываем настройки Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timqwees.settings')

app = Celery('timqwees')

# Загружаем настройки из settings.py (все переменные с префиксом CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматическое обнаружение tasks.py в каждом приложении
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Тестовая задача для проверки работы Celery"""
    print(f'Request: {self.request!r}')
