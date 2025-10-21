from django import forms
from .models import Note, Task
from .crypt import encrypt_data, decrypt_data # Import our functions

class NoteForm(forms.ModelForm):
    # 1. Add a separate, non-model field for 'content'
    content = forms.CharField(widget=forms.Textarea(attrs={'rows': 10}), required=False, label="Content")
    
    # 2. Add a non-model FileField for the upload
    attachment = forms.FileField(required=False, label="Attachment")
    
    class Meta:
        model = Note
        # 3. We only list 'title' here. The other fields are handled manually.
        fields = ['title'] 

    def __init__(self, *args, **kwargs):
        # 4. Call the parent __init__
        super().__init__(*args, **kwargs)
        
        # 5. Decrypt content for editing
        if self.instance and self.instance.pk:
            self.fields['content'].initial = self.instance.content
            # Show the user the name of the file they already have
            if self.instance.attachment_name:
                 # Provide a clear message to the user
                self.fields['attachment'].label = "Replace current file:"
                self.fields['attachment'].help_text = f"Current: {self.instance.attachment_name}"


    def save(self, commit=True):
        # 6. Get the note instance, but don't save it to the DB yet.
        note = super().save(commit=False)
        
        # 7. Encrypt text content (same as before)
        note.encrypted_content = encrypt_data(self.cleaned_data['content'])
        
        # --- 8. NEW: Handle file encryption ---
        uploaded_file = self.cleaned_data.get('attachment')
        if uploaded_file:
            # Pass the file object to our new model method
            note.set_attachment(uploaded_file)
        
        # 9. If commit is True, save the instance to the DB.
        if commit:
            note.save()
        return note

class TimeScheduleForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title','due_date']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }