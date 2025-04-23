from django.urls import path
from . import views

app_name = 'notes'
urlpatterns = [
    path('', views.home, name='home'),
    path('add/note/', views.add_note, name='add_note'),
    path('view/notes/', views.view_notes, name='view_notes'),
    path('view/note/<int:note_id>/', views.note_detail, name='note_detail'),
    path('edit/note/<int:note_id>/', views.edit_note, name='edit_note'),
    path('delete/note/<int:note_id>', views.delete_note, name="delete_note"),
]