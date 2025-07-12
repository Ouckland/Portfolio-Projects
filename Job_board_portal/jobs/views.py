from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import IntegrityError
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import Http404, HttpResponseNotFound, HttpResponseForbidden
from .models import JobApplication, JobPosting, Notification
from .forms import PostJobForm, ApplyForJobForm
from django.utils import timezone
from django.views.decorators.http import require_POST
from users.models import EmployerProfile, SeekerProfile
from .utils import get_user_profile, create_notification, calculate_profile_completion
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt



User = get_user_model()

# Create your views here.

def home(request):
    return render(request, 'app/home.html')

@login_required
def dashboard(request):
    user = request.user
    profile, profile_type = get_user_profile(user)

    if profile is None:
        messages.error(request, "No profile found. Please complete your profile setup.")
        return redirect('users:profile_setup')

    context = {'profile_type': profile_type}

    if profile_type == 'employer':
        context['active_jobs'] = JobPosting.objects.filter(
            employer=profile,
            deadline__gte=timezone.now().date()
        )

        context['total_applications'] = JobApplication.objects.filter(
            job__in=context['active_jobs']
        ).count()

    elif profile_type == 'seeker':
        jobs = JobPosting.objects.filter(
            deadline__gte=timezone.now().date()
        ).exclude(applications__applicant=profile)

        # --- Recommended Jobs Based on Seeker's Skills ---
        recommended_jobs = jobs
        if profile.skills:
            seeker_skills = [s.strip().lower() for s in profile.skills.split(",") if s.strip()]
            skill_query = Q()
            for skill in seeker_skills:
                skill_query |= (
                    Q(title__icontains=skill) |
                    Q(skills_required__icontains=skill) |
                    Q(job_category__icontains=skill)
                )
            recommended_jobs = recommended_jobs.filter(skill_query).distinct()
        else:
            recommended_jobs = recommended_jobs.none()

        context['recommended_jobs'] = recommended_jobs[:5]

        # --- Search & Filtering ---
        search_jobs = jobs
        search_query = request.GET.get('q')
        if search_query:
            search_jobs = search_jobs.filter(
                Q(title__icontains=search_query) |
                Q(location__icontains=search_query) |
                Q(skills_required__icontains=search_query)
            )

        job_type = request.GET.get('job_type')
        if job_type:
            search_jobs = search_jobs.filter(job_type=job_type)

        location = request.GET.get('location')
        if location:
            search_jobs = search_jobs.filter(location__icontains=location)

        sort = request.GET.get('sort')
        if sort == "deadline":
            search_jobs = search_jobs.order_by("deadline")
        else:
            search_jobs = search_jobs.order_by("-posted_date")

        paginator = Paginator(search_jobs, 5)
        page_number = request.GET.get("page")
        context['latest_jobs'] = paginator.get_page(page_number)

        context['job_applications'] = JobApplication.objects.filter(
            applicant=profile
        ).order_by('-application_date')[:5]

    return render(request, 'app/dashboard.html', context)



@login_required
def add_job(request):
    user = request.user

    try:
        profile = user.employerprofile
    except EmployerProfile.DoesNotExist:
        messages.error(request, 'This action is only allowed for employer accounts.')
        return redirect('jobs:forbidden')

    if request.method == 'POST':
        form = PostJobForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                job = form.save(commit=False)
                job.employer = profile
                job.save()
                create_notification(
                    recipient=request.user,
                    message=f'The job {job.title} has been posted succesfully!',
                )
                messages.success(request, 'Job successfully posted.')
                return redirect('jobs:dashboard')
            except IntegrityError:
                messages.error(request, 'There was an error saving the job. Please try again.')
    else:
        form = PostJobForm()

    return render(request, 'app/employer/add-job.html', {'job_form': form})


@login_required
def view_job_detail(request, job_id):
    user = request.user

    try:
        job = get_object_or_404(JobPosting, id=job_id)

        # Optional: Ensure only the employer who posted the job can view its detail
        if hasattr(user, 'employerprofile') and job.employer != user.employerprofile:
            messages.error(request, 'Access denied: You are not authorized to view this job.')
            return redirect('jobs:dashboard')

    except JobPosting.DoesNotExist:
        messages.error(request, 'Job not found.')
        return redirect('jobs:dashboard')

    context = {
        'job': job,
    }
    return render(request, 'app/employer/view-job-detail.html', context)



@login_required
def update_job_details(request, job_id):
    user = request.user

    if not user:
        messages.error(request, 'Session has expired. Try logging in again.')
        return redirect('users:login')

    job = get_object_or_404(JobPosting, id=job_id)
    applications = JobApplication.objects.filter(job=job)

    if job.employer != user.employerprofile:
        messages.error(request, 'You are not authorized to edit this job.')
        return redirect('jobs:dashboard')

    if request.method == 'POST':
        form = PostJobForm(request.POST, request.FILES, instance=job)
        if form.is_valid():
            try:
                form.save()
                
                # Notify the employer
                create_notification(
                    recipient=request.user,
                    message=f"Job details for '{job.title}' have been updated successfully.",
                )

                # Notify each applicant
                for application in applications:
                    try:
                        link = reverse('jobs:update_application', args=[application.id])
                        create_notification(
                            recipient=application.applicant.user,
                            message=(
                                f"The job '{job.title}' you applied for at {job.employer} has been updated. "
                                "Please review and update your application if needed."
                            ),
                            url=link,
                        )
                    except Exception as e:
                        messages.error(request, f"Notification error for applicant {application.applicant}: {e}")

                messages.success(request, 'Job details updated successfully.')
                return redirect('jobs:dashboard')

            except IntegrityError:
                messages.error(request, 'An error occurred while saving the job. Please try again.')

    else:
        form = PostJobForm(instance=job)

    context = {
        'job': job,
        'form': form,
    }

    return render(request, 'app/employer/update-job-details.html', context)


@login_required
def delete_job(request, job_id):
    user = request.user

    if not user:
        messages.error(request, 'Session has expired. Try logging in again.')
        return redirect('users:login')

    job = get_object_or_404(JobPosting, id=job_id)

    # Check permission
    if job.employer != user.employerprofile:
        messages.error(request, 'You do not have permission to delete this job.')
        return redirect('jobs:dashboard')

    # Save job info before deletion
    job_title = job.title
    employer_name = str(job.employer)

    # Get all applications before job is deleted
    applications = job.applications.select_related('applicant__user').all()
        # Delete the job
    if request.method == 'POST':
        job.delete()

        # Notify employer
        create_notification(
            recipient=request.user,
            message=f'Your job "{job_title}" has been successfully deleted.'
        )

        # Notify all applicants
        for application in applications:
            print(f"Sending to {application.applicant.user} for job {job_title}")
            try:
                create_notification(
                    recipient=application.applicant.user,
                    message=f'The job "{job_title}" at {employer_name} you applied for has been removed by the employer.'
                )
            except Exception as e:
                messages.error(request, f"Notification error for applicant {application.applicant}: {e}")

        messages.success(request, 'Job successfully deleted.')
        return redirect('jobs:dashboard')

    return render(request, 'app/employer/delete-job.html', {'job': job})




@login_required
def apply_for_job(request, job_id):
    user = request.user

    if not user:
        messages.error(request, 'Session has expired. Try logging in again.')
        return redirect('users:login')

    job = get_object_or_404(JobPosting, id=job_id)

    try:
        seeker = user.seekerprofile
    except SeekerProfile.DoesNotExist:
        messages.error(request, 'You must have a seeker profile to apply for jobs.')
        return redirect('jobs:dashboard')

    # Check if already applied
    if JobApplication.objects.filter(job=job, applicant=seeker).exists():
        messages.warning(request, 'You have already applied for this job.')
        return redirect('jobs:view_job_detail', job_id=job_id)

    form = ApplyForJobForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = seeker
            application.save()

            create_notification(
                recipient=application.applicant.user,
                message=f"Your application for the role {application.job.title} at {application.job.employer.company_name} has been submtted succesfully",
                url=reverse('jobs:view_application_detail', args=[application.id])
            )
            try:
                create_notification(
                    recipient=application.job.employer.user,
                    message=f"{application.applicant.full_name} has applied for the job {application.job.title}",
                    url=reverse("jobs:view_application_detail", args=[application.id])
                )
            except Exception as e:
                messages.error(request, str(e))
                
            messages.success(request, 'Application submitted successfully.')
            return redirect('jobs:dashboard')
        

    context = {
        'job': job,
        'form': form,
    }
    return render(request, 'app/seeker/apply-for-job.html', context)



@login_required
def view_application_detail(request, application_id):
    user = request.user
    application = get_object_or_404(JobApplication.objects.select_related('job', 'applicant__user', 'job__employer'), id=application_id)

    is_seeker = hasattr(user, 'seekerprofile') and application.applicant == user.seekerprofile
    is_employer = hasattr(user, 'employerprofile') and application.job.employer == user.employerprofile

    if not (is_seeker or is_employer):
        messages.error(request, 'You are not authorized to access this application.')
        return redirect('jobs:dashboard')

    context = {
        'application': application,
        'is_seeker': is_seeker,
        'is_employer': is_employer,
    }
    return render(request, 'app/seeker/view-application-detail.html', context)

@login_required
def review_application(request, application_id):
    user = request.user

    try:
        application = get_object_or_404(JobApplication, id=application_id)
        
        # Only employers who posted the job can review
        if user.is_authenticated and hasattr(user, 'employerprofile'):
            if application.job.employer != user.employerprofile:
                messages.error(request, "You are not authorized to review this application.")
                return redirect('jobs:dashboard')
        else:
            messages.error(request, "You must be an employer to review applications.")
            return redirect('jobs:dashboard')

        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'accept':
                application.status = 'accepted'
                application.save()

                create_notification(
                    recipient=request.user,
                    message=f'You have accepted the application from {application.applicant.full_name} succesfully'
                )
                try:

                    create_notification(
                        recipient=application.applicant.user,
                        message=f"Your application for the role {application.job.title} at {application.job.employer.company_name} has been reviewed and accepted succesfully",
                        url=reverse("jobs:view_application_detail", args=[application.id]),
                    )
                except Exception as e:
                    messages.error(request, str(e))

                messages.success(request, 'Application accepted successfully.')
            elif action == 'reject':
                application.status = 'rejected'
                application.save()

                create_notification(
                    recipient=request.user,
                    message=f'You have rejected the application from {application.applicant.full_name} succesfully'
                )
                
                try:
                    create_notification(
                        recipient=application.applicant.user,
                        message=f"Sadly, your application for the role {application.job.title} at {application.job.employer.company_name} has been reviewed and rejected. Better luck next time",
                        url=reverse("jobs:view_application_detail", args=[application.id]),
                    )
                except Exception as e:
                    messages.error(request, str(e))

                messages.success(request, 'Application rejected successfully.')
            return redirect('jobs:view_applications', job_id=application.job.id)

    except JobApplication.DoesNotExist:
        messages.error(request, 'Application not found.')
        return redirect('jobs:dashboard')

    return render(request, 'app/employer/review-application.html', {'application': application})



@login_required
def view_applications(request, job_id):
    job = get_object_or_404(JobPosting, id=job_id, employer=request.user.employerprofile)
    applications = job.applications.select_related('applicant__user').all()
    return render(request, 'app/employer/view-applications.html', {
        'job': job,
        'applications': applications,
    })


@login_required
def delete_application(request, application_id):
    user = request.user

    if not user:
        messages.error(request, 'Session has expired. Try logging in again.')
        return redirect('users:login')

    application = get_object_or_404(JobApplication, id=application_id)

    # Ensure the user is the owner of the application
    if application.applicant.user != user:
        messages.error(request, 'You are not authorized to delete this application.')
        return redirect('jobs:dashboard')
 
    job_role = application.job.title
    employer = application.job.employer
    applicant = application.applicant.full_name

    if request.method == 'POST':
        application.delete()

        create_notification(
            recipient=request.user,
            message=f'You have deleted your application for the job role {job_role} at {employer.company_name}'
        )
        try:
            create_notification(
                recipient=employer.user,
                message=f'Applicant {applicant} have deleted their application for the job role {job_role} you posted.'
            )
        except Exception as e:
            messages.error(request, str(e))

        messages.success(request, 'Job application deleted successfully.')
        return redirect('jobs:dashboard')

    context = {
        'application': application,
    }

    return render(request, 'app/seeker/delete-application.html', context)




@login_required
def update_application(request, application_id):
    user = request.user
    application = get_object_or_404(JobApplication, id=application_id)

    # Only the applicant can update their own application
    if application.applicant.user != user:
        messages.error(request, 'You are not authorized to edit this application.')
        return redirect('jobs:dashboard')

    # Prevent editing if status is not pending
    if application.status != 'pending':
        messages.warning(request, 'You cannot edit an application that has already been reviewed.')
        return redirect('jobs:view_application_detail', application_id=application.id)

    if request.method == 'POST':
        form = ApplyForJobForm(request.POST, request.FILES, instance=application)
        if form.is_valid():
            form.save()

            # Notify seeker
            create_notification(
                recipient=user,
                message=f'You have successfully updated your application for the role "{application.job.title}" at {application.job.employer.company_name}.',
                url=reverse('jobs:view_application_detail', args=[application.id]),
            )

            # Notify employer
            create_notification(
                recipient=application.job.employer.user,
                message=f'Applicant {application.applicant.full_name} updated their application for your job "{application.job.title}".',
                url=reverse('jobs:view_applications', args=[application.job.id]),
            )

            messages.success(request, 'Job application updated successfully.')
            return redirect('jobs:view_application_detail', application_id=application.id)
    else:
        form = ApplyForJobForm(instance=application)

    return render(request, 'app/seeker/update-application.html', {
        'application': application,
        'form': form,
    })

def forbidden(request):
    return render(request, 'error-pages/forbidden.html', )


@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    return render(request, 'app/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })


@login_required
def mark_notification_as_read(request, notification_id):
    if request.method == 'POST':
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        if not notification.is_read:
            notification.is_read = True
            notification.save()
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return JsonResponse({'success': True, 'unread_count': unread_count})
    return JsonResponse({'success': False}, status=400)


@login_required
def mark_all_as_read(request):
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True, 'unread_count': 0})
    return JsonResponse({'success': False}, status=400)


