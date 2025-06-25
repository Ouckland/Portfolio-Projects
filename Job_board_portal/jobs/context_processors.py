from .models import Notification

def user_notifications(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
        unread_count = notifications.filter(is_read=False).count()
        return {
            'notifications': notifications,
            'unread_count': unread_count
        }
    return {}

