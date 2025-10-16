from django import forms
from .models import Note, Task

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'content', 'attachment']

class TimeScheduleForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title','due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }