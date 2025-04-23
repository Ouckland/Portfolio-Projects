from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import login_required

from .forms import NoteForm, SearchNoteForm, FilterByForm
from .models import Note, User
# Create your views here.

def home(request):
    return render(request, 'pages/home.html')

@login_required
def add_note(request):
    note_form = NoteForm(request.POST)
    if request.method == 'POST':
        if note_form.is_valid():
            note_form = NoteForm(request.POST)
            note = note_form.save(commit=False)
            note.added_by = request.user
            note.save()
            messages.success(request, "Note created succesfully.")
        return redirect('notes:view_notes')
    context = {
        "note_form": note_form
    }
    return render(request, 'pages/add-note.html', context)

@login_required
def view_notes(request):
    all_notes = Note.objects.filter(added_by=request.user)
    search_form = SearchNoteForm(request.GET)
    if search_form.is_valid():
        title = search_form.cleaned_data.get('title')
        if title:
            all_notes = all_notes.filter(title__icontains=title)
    
    
    filter_form = FilterByForm(request.GET)
    
    if filter_form.is_valid():
        category = filter_form.cleaned_data.get('category')
        if category:
            all_notes = all_notes.filter(category=category)
    context = {
        'all_notes': all_notes,
        'filter_form': filter_form,
    }
    return render(request, 'pages/view-notes.html', context)

@login_required
def note_detail(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    if request.user != note.added_by:
        messages.error(request, 'You are not permitted to view this notes')
        return redirect('notes:home')
    
    context = {
        'note': note,
    }

    return render(request, 'pages/note.html', context)

@login_required
def edit_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    if request.user != note.added_by:
        messages.error(request, 'You are not permitted to edit this note')
        return redirect('notes:home')

    edit_form = NoteForm(instance=note)
    if request.method == 'POST':
        edit_form = NoteForm(request.POST, instance=note)
        if edit_form.is_valid():
            edit_form.save()
            messages.success(request, 'Note edited succesfully')
        return redirect(reverse('notes:note_detail', kwargs={'note_id': note_id}))


    context = {
        'edit_form': edit_form,
        "note": note,
    }
    return render(request, 'pages/edit-note.html', context)

@login_required
def delete_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    if request.user != note.added_by:
        messages.error(request, 'You are not permitted to delete this note')
        return redirect('notes:home')

    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Note deleted succesfully')
        return redirect('notes:view_notes')
    
    context = {
        "note": note
    }
    return render(request, 'pages/delete.html', context)
