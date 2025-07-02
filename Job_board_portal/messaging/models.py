from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

def get_default_receiver():
    return User.objects.first().id  # Or any logic to return a valid User ID


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    body = models.TextField()

    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender} → {self.receiver}: {self.body[:30]}"

    def get_sender_profile(self):
        return getattr(self.sender, 'seekerprofile', getattr(self.sender, 'employerprofile', None))

    def get_receiver_profile(self):
        return getattr(self.receiver, 'seekerprofile', getattr(self.receiver, 'employerprofile', None))
        
