"""Инициализация Celery при запуске Django"""
import sys

# Python 3.14 fix: django-unfold + Django context.copy() bug
# В Python 3.14 object.__copy__() изменился, ломая BaseContext.__copy__
# Патчим Context.new() чтобы не использовать copy()
if sys.version_info >= (3, 14):
    from django.template.context import Context, RequestContext, BaseContext

    def _safe_new(self, values=None):
        """Замена Context.new() без использования copy()"""
        if values is None:
            values = {}
        # Создаем новый контекст с учетом типа
        if hasattr(self, 'request'):
            new_context = type(self)(request=self.request, dict_=values)
        else:
            new_context = type(self)(dict_=values)
        # Копируем атрибуты
        for attr in ('autoescape', 'use_l10n', 'use_tz', 'template_name', '_processors_index'):
            if hasattr(self, attr):
                setattr(new_context, attr, getattr(self, attr))
        return new_context

    Context.new = _safe_new

from .celery import app as celery_app

__all__ = ('celery_app',)
