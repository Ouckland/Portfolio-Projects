from django import forms 
from .models import Note, Category
class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = [
            'title','content','category'
        ]

class SearchNoteForm(forms.Form):
    title = forms.CharField(max_length=100, required=False)


class FilterByForm(forms.Form):
    category = forms.ChoiceField(choices=Category.choices, required=False)