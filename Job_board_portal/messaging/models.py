# messaging/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

def get_default_receiver():
    return User.objects.first().id  # Or any logic to return a valid User ID

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', default=get_default_receiver)
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"From {self.sender} to {self.receiver}"
