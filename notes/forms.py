from django import forms
from .models import Note, Task
from .crypt import encrypt_data, decrypt_data # Import our functions

class NoteForm(forms.ModelForm):
    # (This form is unchanged)
    content = forms.CharField(widget=forms.Textarea(attrs={'rows': 10}), required=False, label="Content")
    attachment = forms.FileField(required=False, label="Attachment")
    
    class Meta:
        model = Note
        fields = ['title'] 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            self.fields['content'].initial = self.instance.content
            if self.instance.attachment_name:
                self.fields['attachment'].label = "Replace current file:"
                self.fields['attachment'].help_text = f"Current: {self.instance.attachment_name}"

    def save(self, commit=True):
        note = super().save(commit=False)
        note.encrypted_content = encrypt_data(self.cleaned_data['content'])
        
        uploaded_file = self.cleaned_data.get('attachment')
        if uploaded_file:
            note.set_attachment(uploaded_file)
        
        if commit:
            note.save()
        return note

class TimeScheduleForm(forms.ModelForm):
    # --- FIX: Explicitly define title widget to ensure 'form-control' class is present ---
    title = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Task
        # --- REMOVED 'parent' from fields list ---
        fields = ['title','due_date']
        widgets = {
            'due_date': forms.DateTimeInput(
                attrs={
                    'type': 'text', 
                    'class': 'form-control datetime-picker',
                    'placeholder': 'Select date and time...'
                }
            ),
        }
    
    # --- The __init__ method has been REMOVED ---