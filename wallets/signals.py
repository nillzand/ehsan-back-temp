# wallets/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from companies.models import Company
from .models import Wallet

@receiver(post_save, sender=Company)
def create_company_wallet(sender, instance, created, **kwargs):
    """
    A signal to automatically create a Wallet the first time a Company is created.
    """
    if created:
        Wallet.objects.create(company=instance)