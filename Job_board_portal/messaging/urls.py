from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('chat/all/', views.chat_list_view, name='all_chats'),
    path('chat/<str:username>/', views.chat_view, name='chat_view'),
        path('typing/<str:username>/', views.typing_status, name='typing_status'),

]


