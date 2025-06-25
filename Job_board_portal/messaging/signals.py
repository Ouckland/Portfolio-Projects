from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message

@receiver(post_save, sender=Message)
def notify_receiver(sender, instance, created, **kwargs):
    if created:
        # Notify the receiver - e.g., update a Notification model, or send an email
        print(f"New message to {instance.receiver.username} from {instance.sender.username}")
