from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('view-profile', views.profile, name='view_profile'),

    # Employers url
    path('add-job/', views.add_job, name='add_job'),
    path('view-job-detail/<int:job_id>/', views.view_job_detail, name='view_job_detail'),
    path('update-job/<int:job_id>/', views.update_job_details, name='update_job_details'),
    path('delete-job/<int:job_id>/', views.delete_job, name='delete_job'),
    path('view-applications/<int:job_id>/', views.view_applications, name='view_applications'),
    
    # Seekers url
    path('apply-for-job/<int:job_id>/', views.apply_for_job, name='apply_for_job'),
    path('view-application/<int:application_id>/', views.view_application_detail, name='view_application_detail'),
    path('update-application/<int:application_id>/', views.update_application, name='update_application'),
    path('delete-application/<int:application_id>/', views.delete_application, name='delete_application'),
    path('review-application/<int:application_id>/', views.review_application, name='review_application'),


    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/read/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('notifications/mark-all-as-read/', views.mark_all_as_read, name='mark_all_as_read'),
    path('profile/update/', views.update_profile, name='update_profile'),   
    path('profile/update/basic-info/', views.update_basic_info, name='update_basic_info'),   
    path('profile/update/account-info/', views.update_account_info, name='update_account_info'),
    path('update-picture/', views.update_profile_picture, name='update_profile_picture'),   
    path('404-forbidden/', views.forbidden, name='forbidden'),
    path('profile/<str:username>/', views.public_profile, name='public_profile'),
    
]
