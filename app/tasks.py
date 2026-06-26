"""Celery задачи для приложения"""
from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta


@shared_task
def send_order_confirmation_email(order_id: int, email: str, username: str) -> str:
    """Асинхронная отправка письма подтверждения заказа (Mailhog)"""
    send_mail(
        subject=f'Заказ #{order_id} оформлен!',
        message=f'Здравствуйте, {username}! Ваш заказ #{order_id} успешно оформлен и принят в обработку.',
        from_email='noreply@timqwees.com',
        recipient_list=[email],
        fail_silently=False,
    )
    return f'Письмо отправлено для заказа #{order_id}'


@shared_task
def cleanup_old_orders(days: int = 90) -> str:
    """Периодическая задача: удаление старых отмененных заказов"""
    from app.models import Order
    cutoff_date = timezone.now() - timedelta(days=days)
    old_orders = Order.objects.filter(
        status='cancelled',
        created_at__lt=cutoff_date
    )
    count = old_orders.count()
    old_orders.delete()
    return f'Удалено {count} старых отмененных заказов'


@shared_task
def notify_order_status_change(order_id: int, new_status: str) -> str:
    """Уведомление об изменении статуса заказа"""
    from app.models import Order
    try:
        order = Order.objects.select_related('customer').get(id=order_id)
        status_display = dict(Order.STATUS_CHOICES).get(new_status, new_status)
        send_mail(
            subject=f'Статус заказа #{order_id} изменен',
            message=f'Статус вашего заказа #{order_id} изменен на: {status_display}',
            from_email='noreply@timqwees.com',
            recipient_list=[order.customer.email] if order.customer.email else [],
            fail_silently=True,
        )
        return f'Уведомление отправлено для заказа #{order_id}'
    except Order.DoesNotExist:
        return f'Заказ #{order_id} не найден'
