from django import forms
from .models import Note

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'content', 'due_date', 'attachment']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }
