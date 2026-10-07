from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserCreditProfile


@receiver(post_save, sender=get_user_model())
def create_user_credit_profile(sender, instance, created, **kwargs):
    if created:
        UserCreditProfile.objects.create(user=instance)
