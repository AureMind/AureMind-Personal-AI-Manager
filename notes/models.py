from django.db import models
from django.contrib.auth.models import User

class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    due_date = models.DateField(null=True, blank=True)
    attachment = models.FileField(upload_to='attachments/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Task(models.Model):
    title = models.CharField(max_length=200)
    note = models.OneToOneField(Note, on_delete=models.CASCADE, primary_key=True)
    due_date = models.DateField()

    def __str__(self):
        return f"Schedule for {self.note.title}"