from django.db import models
from django.core.validators import MinLengthValidator
from django.contrib.auth import get_user_model
from django.conf import settings


# Create your models here.
User = get_user_model()
class Category(models.TextChoices):
    work = "WRK", "Work"
    personal = "PSNL", "Personal"
    ideas = "IDE", "Ideas"
    study = "STY", "Study"



class Note(models.Model):
    title = models.CharField(max_length=100, validators=[MinLengthValidator(3)], help_text="Title of the note")
    content = models.TextField()
    category = models.CharField(max_length=4, choices=Category.choices, default=Category.personal)
    date_created = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, default=6)

    def __str__(self):
        return f"{self.title} - {self.category}"
    
