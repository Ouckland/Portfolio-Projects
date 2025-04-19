from .models import Recipe
from django import forms

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = [
            "name","ingredients","instructions","cooking_time","dish_image",
        ]

class SearchForm(forms.Form):
    name = forms.CharField(max_length=255, required=False)