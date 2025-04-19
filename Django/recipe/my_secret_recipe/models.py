from django.db import models

# Create your models here.
class Recipe(models.Model):
    name = models.CharField(max_length=255, help_text="Name of the Recipe")
    ingredients = models.TextField(help_text="Comma-separated ingredients")
    instructions = models.TextField(help_text="Cooking instructions")
    cooking_time = models.PositiveIntegerField(help_text="Time in minutes")
    dish_image = models.ImageField(upload_to='dish_image/', blank=True, null=True)

    def __str__(self):
        return f"{self.name}"