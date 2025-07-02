from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Message
from .forms import MessageForm
from jobs.models import Notification  # Import your Notification model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timesince import timesince
from django.urls import reverse
from jobs.utils import get_user_profile  # if you have this helper
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils.timesince import timesince
from .models import Message



@csrf_exempt
@login_required
def typing_status(request, username):
    # Use Django cache to store typing status for a short time
    from django.core.cache import cache
    key = f"typing_{username}_to_{request.user.username}"
    if request.method == "POST":
        cache.set(key, True, timeout=5)  # Typing status lasts 5 seconds
        return JsonResponse({"status": "ok"})
    if request.method == "GET":
        is_typing = cache.get(key, False)
        return JsonResponse({"typing": is_typing})


@login_required
def chat_view(request, username):
    receiver = get_object_or_404(User, username=username)
    chat_messages = Message.objects.filter(
        sender__in=[request.user, receiver],
        receiver__in=[request.user, receiver]
    ).order_by('timestamp')

    # Mark all messages from receiver to user as read
    if request.GET.get('ajax') == '1':
        Message.objects.filter(
            sender=receiver,
            receiver=request.user,
            is_read=False
        ).update(is_read=True)

        messages_data = []
        for msg in chat_messages:
            # Get profile picture
            profile_pic = None
            try:
                profile_pic = msg.sender.seekerprofile.profile_picture.url
            except:
                try:
                    profile_pic = msg.sender.employerprofile.company_logo.url
                except:
                    profile_pic = None
            messages_data.append({
                "sender": msg.sender.username,
                "body": msg.body,
                "is_read": msg.is_read,
                "profile_pic": profile_pic,
            })
        return JsonResponse({
            "messages": messages_data,
            "receiver_name": receiver.get_full_name() or receiver.username,
            "current_user": request.user.username,
        })






@login_required
def chat_list_view(request):
    user = request.user

    # Get all users this user has chatted with
    conversations = Message.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).order_by('-timestamp')

    # ...existing code...
    unique_partners = {}
    for msg in conversations:
        partner = msg.receiver if msg.sender == user else msg.sender

        if partner not in unique_partners:
            # Get their profile (seeker or employer)
            try:
                profile = partner.seekerprofile
            except:
                profile = partner.employerprofile

            # Count unread messages from this partner to the user
            unread_count = Message.objects.filter(
                sender=partner,
                receiver=user,
                is_read=False
            ).count()

            unique_partners[partner] = {
                'profile': profile,
                'latest_message': msg,
                'unread_count': unread_count,
            }

    return render(request, 'messaging/inbox.html', {
        'chat_partners': unique_partners
    })
