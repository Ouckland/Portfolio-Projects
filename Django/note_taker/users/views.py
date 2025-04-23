from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages

# Create your views here.
def sign_up(request):
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created succesfully")
            return redirect('users:login')
    context = {
        "form": form
    }
    return render(request, 'users/sign-up.html', context)    
    
class CustomLoginView(SuccessMessageMixin, LoginView):
    success_message = "Succesfully logged in"

class CustomLogoutView(SuccessMessageMixin, LogoutView):
    success_message = "Succesfully Logged out"