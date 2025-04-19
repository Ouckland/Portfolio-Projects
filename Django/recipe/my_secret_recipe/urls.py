from django.urls import path
from . import views

app_name = 'my_secret_recipe'
urlpatterns = [
    path('add-recipe/', views.add_recipe, name="add_recipe"),
    path('view-recipe/', views.view_recipes, name="view_recipes"),
    path('delete-recipe/<int:recipe_id>/', views.delete_recipe, name="delete_recipe"),
    path('edit-recipe/<int:recipe_id>/', views.edit_recipe,name="edit_recipe"),
]
