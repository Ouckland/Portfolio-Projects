from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('chat/<str:username>/', views.chat_view, name='chat_view'),
]
