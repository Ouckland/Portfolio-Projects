from django.utils.html import format_html
from django.utils import timezone
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MinLengthValidator
from users.models import EmployerProfile, SeekerProfile, User
# Create your models here.

class JobType(models.TextChoices):
    ft = 'FT', 'Full-Time'
    pt = 'PT', 'Part-Time'

class JobStatus(models.TextChoices):
    closed = 'closed', 'Closed'
    open = 'open', 'Open'

class Status(models.TextChoices):
    pending = 'pending', 'PENDING'
    accepted = 'accepted', 'ACCEPTED'
    rejected = 'rejected', 'REJECTED'

class JobPosting(models.Model):
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name='posted_jobs')
    title = models.CharField(max_length=255, validators=[MinLengthValidator(3)])
    job_type = models.CharField(max_length=50, choices=JobType.choices, default=JobType.ft)
    location = models.CharField(max_length=255)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    experience_required = models.PositiveIntegerField(help_text='In years')
    qualifications = models.TextField()
    posted_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField()
    job_category = models.CharField()
    job_status = models.CharField(max_length=50, choices=JobStatus.choices, default=JobStatus.open)
    skills_required = models.CharField()
    # job_id = models.ForeignKey(JobId, on_delete=models.CASCADE)

    unique_together = ('employer', 'title')
        
    def is_active(self):
        return self.deadline >= timezone.now().date()
    
    def verify_job_status(self):
        if self.is_active():
            return format_html('<span style="color: green;">Open</span>')
        else:
            return format_html('<span style="color: red;">Closed</span>')

    def __str__(self):
        return f'{self.title} at {self.employer.company_name}'
    
    
class JobApplication(models.Model):
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(SeekerProfile, on_delete=models.CASCADE)
    application_date = models.DateTimeField(auto_now_add=True)
    cover_letter = models.TextField()
    resume = models.FileField(upload_to='resumes/')
    attachments = models.FileField(upload_to='attachments/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.pending)

    class Meta:
        unique_together = ('job', 'applicant')

    def clean(self):
        if self.job_id and self.job.deadline < timezone.now().date():
            raise ValidationError('Job application has closed.')
            

    def __str__(self):
        return f'{self.applicant.full_name} applied for {self.job.title}'

    

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    url = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Notification to {self.recipient.username}'


