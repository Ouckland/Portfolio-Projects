from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
]