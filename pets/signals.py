from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Pet


@receiver(post_save, sender=Pet)
def update_seller_stats_on_save(sender, instance, **kwargs):
    """Update seller statistics when a pet is saved."""
    if not kwargs.get('raw', False):
        instance.seller.update_stats()


@receiver(post_delete, sender=Pet)
def update_seller_stats_on_delete(sender, instance, **kwargs):
    """Update seller statistics when a pet is deleted."""
    instance.seller.update_stats()
