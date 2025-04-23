from django.urls import path
from django.contrib.auth import views as user_view
from . import views

app_name = 'users'
urlpatterns = [
    path('sign/up/', views.sign_up, name="sign_up"),
    path('login/', views.CustomLoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout', views.CustomLogoutView.as_view(), name="logout"),
]
