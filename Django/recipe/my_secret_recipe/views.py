from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse

from .models import Recipe
from .forms import RecipeForm, SearchForm

# Create your views here.
def add_recipe(request):
    form = RecipeForm()
    if request.method == "POST":
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            print(request.POST)
            form.save()
            messages.success(request, "Recipe created succesfully")
            return redirect(reverse('my_secret_recipe:view_recipes'))
    
    context = {
        "form": form,
    }
    return render(request, 'pages/add-recipe.html', context)

def view_recipes(request):
    recipes = Recipe.objects.all()
    search_form = SearchForm(request.GET)
    # sort_field = request.GET.get('sort', 'name')

    if search_form.is_valid():
        name = search_form.cleaned_data.get('name')
        if name:
            recipes = recipes.filter(name__icontains=name)

    # recipes = recipes.order_by(_sort_field)
    context = {
        "recipes": recipes,
    }

    return render(request, 'pages/view-recipes.html', context)

def delete_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    if request.method == 'POST':
        recipe.delete()
        messages.success(request, 'Recipe succesfully deleted')
        return redirect('my_secret_recipe:view_recipes', )
    return render(request, 'pages/delete-recipe.html')

def edit_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    form = RecipeForm(instance=recipe)
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        if form.is_valid():
            form.save()
            messages.success(request, "Recipe succesfully edited")
            return redirect('my_secret_recipe:view_recipes')
        
    context = {
        "form": form,
        "recipe": recipe
    }
    return render(request, 'pages/edit-recipe.html', context)