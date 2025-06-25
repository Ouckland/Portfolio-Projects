from .models import Message

def get_unread_message_count(user):
    return Message.objects.filter(receiver=user, is_read=False).count()
