import random
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from jobs.utils import create_notification
from .models import OTP, Profile, EmployerProfile, SeekerProfile, KnownDevice, SecurityLog
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from .models import State, Country



from .forms import EmailSignupForm, User, OTPform, ChooseAccountTypeForm, EmployerBasicInfoForm, SeekerBasicInfoForm
from .forms import EmployerAccountForm, SeekerAccountForm, LoginForm , PasswordResetRequestForm, PasswordResetForm

User = get_user_model()


def email_signup_view(request):
    if request.method == 'POST':
        form = EmailSignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')

            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already in use! Try another one or log in.')
                return redirect('users:email_sign_up')

            # Check for existing OTP
            existing_otp = OTP.objects.filter(user_email=email).first()
            if existing_otp:
                if existing_otp.is_expired:
                    existing_otp.delete()  # clean up expired OTP so we can generate a new one
                else:
                    messages.error(request, 'OTP already sent to this email. Please wait or check your inbox.')
                    return redirect('users:email_sign_up')

            # Generate new OTP
            otp = str(random.randint(100000, 999999))

            # Save new OTP to DB
            OTP.objects.update_or_create(
                user_email=email,
                defaults={'otp': otp, 'created_at': timezone.now()}
            )

            # Save signup data in session
            request.session['signup_email'] = email
            request.session['signup_form_data'] = form.cleaned_data

            # Send OTP
            try:
                send_mail(
                    subject='Email OTP Verification',
                    message=f"Hello,\n\nYour OTP for account creation is: {otp}\n\n- Jobsphere",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as e:
                messages.error(request, f"Failed to send OTP: {str(e)}")
                return redirect('users:email_sign_up')

            messages.success(request, f'OTP sent to {email}')
            return redirect('users:validate_otp', user_email=email)
    else:
        form = EmailSignupForm()

    return render(request, 'user/signup.html', {'form': form})


def validate_otp(request, user_email):
    signup_data = request.session.get('signup_form_data')
    if not signup_data:
        messages.error(request, 'Session expired. Please try signing up again.')
        return redirect('users:email_signup')

    otp_form = OTPform(user_email=user_email)

    if request.method == 'POST':
        # Combine the 6 input boxes into a single 'otp' field in the template JS
        otp_form = OTPform(request.POST, user_email=user_email)
        if otp_form.is_valid():
            entered_otp = otp_form.cleaned_data.get('otp')
            try:
                otp_object = OTP.objects.get(user_email=user_email)
                if entered_otp == otp_object.otp:
                    otp_object.delete()
                    messages.success(request, 'OTP verified successfully. Please complete your profile to proceed.')
                    return redirect('users:choose_account_type')
                else:
                    messages.error(request, 'Invalid OTP. Please try again.')
            except OTP.DoesNotExist:
                messages.error(request, 'OTP has expired or does not exist.')
        else:
            # This will catch cases like not entering all 6 digits
            messages.error(request, 'Please enter a valid 6-digit OTP.')

    return render(request, 'user/validate-otp.html', {'form': otp_form, 'user_email': user_email})


def resend_otp(request, user_email):
    user_email = request.session.get('signup_email')
    if not user_email:
        messages.error(request, 'Session expired. Please try signing up again.')
        return redirect('users:email_sign_up')

    if request.method == 'GET':
        otp = OTP.objects.get(user_email=user_email)
        if not otp.is_expired:
            messages.error(request, 'OTP code is still valid. Wait for a while and try again!')
            return redirect('users:validate_otp', user_email=user_email)    
        
        # Generate OTP
        otp = str(random.randint(100000, 999999))

        # Store OTP in the database or update if it already exists
        OTP.objects.update_or_create(
            user_email=user_email,
            defaults={'otp': otp, 'created_at': timezone.now()}
        )

        send_mail(
                subject='Email OTP Verification',
                message=f"Hello,\n\nYour OTP for account creation is: {otp}\n\n- Jobsphere",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False
            )

        messages.info(request, f'OTP sent to {user_email}')
        return redirect('users:validate_otp', user_email=user_email)
    return render(request, 'user/validate-otp.html', {'user_email': user_email})


def choose_account_type_view(request):
    user_email = request.session.get('signup_email')
    sign_up_data = request.session.get('signup_form_data')
    
    if not user_email or not sign_up_data:
        messages.error(request, "Session expired. Please restart the sign-up process.")
        return redirect('users:email_signup')

    password = sign_up_data.get('password')
    form = ChooseAccountTypeForm(user_email=user_email)

    if request.method == 'POST':
        form = ChooseAccountTypeForm(user_email=user_email, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            account_type = form.cleaned_data.get('account_type')

            # Check if username already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists! Please try another one.")
                return redirect('users:choose_account_type')

            # Create user
            user = User.objects.create_user(
                username=username,
                email=user_email,
                password=password
            )
            user.is_active = False  # Will activate after completing profile
            user.save()

            # Create appropriate profile
            if account_type == 'seeker':
                SeekerProfile.objects.create(user=user, account_type='seeker')
            elif account_type == 'employer':
                EmployerProfile.objects.create(user=user, account_type='employer')

            # Store info in session for next steps
            request.session['pending_user_id'] = user.id
            request.session['account_type'] = account_type

            return redirect('users:basic_info')  # Go to next setup step

    return render(request, 'user/account-type.html', {'form': form})


def basic_info_view(request):
    user_id = request.session.get('pending_user_id')

    if not user_id:
        return redirect('users:choose_account_type')  # Redirect if user hasn't been created

    user = User.objects.get(id=user_id)  # Get the user from the session data
    account_type = request.session.get('account_type')

    # Define forms based on account type
    if account_type == 'employer':
        form = EmployerBasicInfoForm()
    else:
        form = SeekerBasicInfoForm()

    if request.method == 'POST':
        form = form.__class__(request.POST, request.FILES)  # Handle form submission
        if form.is_valid():
            # Convert model instances to IDs for session storage
            basic_info = form.cleaned_data.copy()
            for key, value in basic_info.items():
                if hasattr(value, 'pk'):
                    basic_info[key] = value.pk
            request.session['basic_info'] = basic_info
            return redirect('users:account_info')  # Go to the account info page to fill out more data

    countries = Country.objects.all().order_by('name')
    states = State.objects.all().order_by('name')
    return render(request, 'user/basic-info.html', {
        'form': form,
        'countries': countries,
        'states': states,
    })

def account_info_view(request):
    user_id = request.session.get('pending_user_id')
    account_type = request.session.get('account_type')

    if not user_id or not account_type:
        messages.error(request, "Session expired or invalid. Please sign up again.")
        return redirect('users:signup')

    user = get_object_or_404(User, id=user_id)
    basic_info_data = request.session.get('basic_info', {})

    if account_type == 'seeker':
        profile, _ = SeekerProfile.objects.get_or_create(user=user)
        FormClass = SeekerAccountForm
        basic_fields = ['full_name', 'phone_number', 'country', 'state', 'bio']
    else:
        profile, _ = EmployerProfile.objects.get_or_create(user=user)
        FormClass = EmployerAccountForm
        basic_fields = ['company_name', 'contact_number', 'country', 'state', 'description']

    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)

            # Assign related model instances for country and state
            for field in basic_fields:
                value = basic_info_data.get(field, getattr(profile, field))
                if field == "country" and value:
                    value = Country.objects.get(pk=value)
                if field == "state" and value:
                    value = State.objects.get(pk=value)
                setattr(profile, field, value)

            profile.save()
            user.is_active = True
            user.save()
            request.session.flush()
            request.session['show_welcome_notification'] = True
            messages.success(request, "Account setup successful. Please log in.")
            return redirect('users:login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = FormClass(instance=profile)

    return render(request, 'user/account-info.html', context={'form': form, 'account_type': account_type})




def login_view(request):
    form = LoginForm()

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)

                # Welcome notification from session
                if request.session.get('show_welcome_notification'):
                    create_notification(
                        recipient=user,
                        message="Welcome! Your account and profile setup is complete. You're all set to get started.",
                        url=reverse('jobs:dashboard'),
                    )
                    request.session.pop('show_welcome_notification', None)

                current_agent = request.META.get('HTTP_USER_AGENT', '')

                # ✅ Check if device is already known in DB
                if not KnownDevice.objects.filter(user=user, user_agent=current_agent).exists():
                    # Unfamiliar device login
                    create_notification(
                        recipient=user,
                        message="New login detected from an unfamiliar device or browser.",
                        url=reverse('jobs:dashboard'),
                    )

                    # Save device
                    KnownDevice.objects.create(user=user, user_agent=current_agent)

                create_notification(
                    recipient=user,
                    message="You've logged in successfully.",
                    url=reverse('jobs:dashboard'),
                )

                messages.success(request, 'Login successful.')
                return redirect('jobs:dashboard')

            else:
                messages.error(request, 'Invalid credentials.')
    return render(request, 'user/login.html', {'form': form})


def forgot_password(request):
    form = PasswordResetRequestForm()
    
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data.get('email')
            try:
                user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                messages.error(request, 'No account found with that email')
                return redirect('users:forgot_password')

            # Generate OTP
            otp = str(random.randint(100000, 999999))
            OTP.objects.update_or_create(
                user_email=user_email,
                defaults={'otp': otp, 'created_at': timezone.now()}
            )

            send_mail(
                subject='Password Reset OTP',
                message=f"Hello,\n\nYour OTP for resetting your password is: {otp}\n\n- Jobsphere",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False
            )

            request.session['user_email'] = user_email
            messages.info(request, f'OTP sent to {user_email}')
            return redirect('users:validate_reset_otp', user_email=user_email)

    return render(request, 'user/forgot-password.html', {'form': form})
def validate_reset_otp(request, user_email):
    # Make sure we use the email from session only
    user_email = request.session.get('user_email')

    if not user_email:
        messages.error(request, 'Session expired. Please try again.')
        return redirect('users:forgot_password')

    form = OTPform(user_email=user_email)

    if request.method == 'POST':
        form = OTPform(request.POST, user_email=user_email)
        if form.is_valid():
            entered_otp = form.cleaned_data.get('otp')
            try:
                otp_object = OTP.objects.get(user_email=user_email)

                if entered_otp == otp_object.otp:
                    otp_object.delete()

                    # Set a session key to allow password reset
                    request.session['allow_password_reset'] = True

                    messages.success(request, 'OTP verified. You can now reset your password.')
                    return redirect('users:reset_password')  # 👈 no need to pass email in URL

                else:
                    messages.error(request, 'Invalid OTP. Please try again.')

            except OTP.DoesNotExist:
                messages.error(request, 'OTP has expired or does not exist. Please request a new one.')

        else:
            messages.error(request, 'Please enter a valid OTP.')

    return render(request, 'user/validate-reset-otp.html', {'form': form, 'user_email': user_email})


def resend_reset_otp(request, user_email):
    user_email = request.session.get('user_email')
    if not user_email:
        messages.error(request, 'Session expired. Please try again.')
        return redirect('users:forgot_password')

    try:
        existing_otp = OTP.objects.get(user_email=user_email)
        if not existing_otp.is_expired:
            messages.warning(request, 'OTP is still valid. Wait for it to expire before requesting a new one.')
            return redirect('users:validate_reset_otp', user_email=user_email)
    except ObjectDoesNotExist:
        pass  # No OTP exists — we can generate a new one

    # Generate and save new OTP
    new_otp = str(random.randint(100000, 999999))
    OTP.objects.update_or_create(
        user_email=user_email,
        defaults={'otp': new_otp, 'created_at': timezone.now()}
    )

    try:
        send_mail(
            subject='Password Reset Verification',
            message=f"Hello,\n\nYour OTP for password reset is: {new_otp}\n\n- Jobsphere",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False
        )
    except Exception as e:
        messages.error(request, 'There was a problem sending the OTP. Please try again.')
        return redirect('users:forgot_password')

    messages.success(request, f'A new OTP has been sent to {user_email}')
    return redirect('users:validate_reset_otp', user_email=user_email)


def reset_password(request):
    user_email = request.session.get('user_email')
    if not user_email:
        messages.error(request, 'Session has expired, please try again')
        return redirect('users:forgot_password')

    form = PasswordResetForm()
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data.get('password')
            try:
                user = User.objects.get(email=user_email)
                user.set_password(password)
                user.save()

                # Clear session after reset
                request.session.flush()

                create_notification(
                    recipient=user,
                    message="Your password has been reset successfully.",
                )
                SecurityLog.objects.create(
                    user=user,
                    event="Password Reset",
                    ip_address=request.META.get("REMOTE_ADDR"),
                    user_agent=request.META.get("HTTP_USER_AGENT", "")
)


                messages.success(request, 'Password reset successful. Login to continue.')
                return redirect('users:login')

            except User.DoesNotExist:
                messages.error(request, 'User not found.')
                return redirect('users:forgot_password')

    return render(request, 'user/reset-password.html', {'form': form, 'user_email': user_email})



def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'Logged out succesfully.')
        return redirect('jobs:home')
    
    return render(request, 'partials/header.html')

def load_states(request):
    country_id = request.GET.get('country')
    states = State.objects.filter(country_id=country_id).order_by('name')
    # Only return id and name, not the whole object
    return JsonResponse(list(states.values('id', 'name')), safe=False)