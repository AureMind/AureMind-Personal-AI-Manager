from django import forms
from .models import Note,TimeSchedule

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'content', 'attachment']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }
class TimeScheduleForm(forms.ModelForm):
    class Meta:
        model = TimeSchedule
        fields = ['due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }