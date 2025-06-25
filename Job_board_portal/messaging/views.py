from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from .models import Message
from .forms import MessageForm


from jobs.models import Notification  # Import your Notification model
from django.urls import reverse

@login_required
def chat_view(request, username):
    receiver = get_object_or_404(User, username=username)
    messages = Message.objects.filter(
        sender__in=[request.user, receiver],
        receiver__in=[request.user, receiver]
    ).order_by('timestamp')

    # Mark unread messages as read
    messages.filter(receiver=request.user, is_read=False).update(is_read=True)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.receiver = receiver
            msg.save()

            # ✅ Create a Notification for the receiver
            Notification.objects.create(
                recipient=receiver,
                message=f"You have a new message from {request.user.username}",
                url=request.build_absolute_uri(
                    reverse('messaging:chat_view', kwargs={'username': request.user.username})
                )
            )

            return redirect('messaging:chat_view', username=receiver.username)
    else:
        form = MessageForm()

    return render(request, 'messaging/chat.html', {
        'receiver': receiver,
        'messages': messages,
        'form': form,
    })
