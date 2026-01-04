from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from app.models import Order


class Command(BaseCommand):
    help = 'Удаляет старые отмененные заказы (старше 90 дней)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Количество дней для удаления заказов (по умолчанию 90)',
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)

        old_orders = Order.objects.filter(
            status='cancelled',
            created_at__lt=cutoff_date
        )

        count = old_orders.count()
        old_orders.delete()

        self.stdout.write(
            self.style.SUCCESS(f'Удалено {count} отмененных заказов старше {days} дней')
        )
