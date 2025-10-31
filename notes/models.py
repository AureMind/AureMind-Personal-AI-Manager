from django.db import models
from django.contrib.auth.models import User
from .crypt import encrypt_data, decrypt_data
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

# Get the raw Fernet object for byte encryption
try:
    f = Fernet(settings.FERNET_KEY)
except Exception as e:
    raise ValueError(f"Invalid FERNET_KEY in settings.py. It must be a valid Fernet key. Error: {e}")

class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    
    # Rename 'content' to 'encrypted_content'
    encrypted_content = models.TextField(blank=True, null=True, db_column='content')
    created_at = models.DateTimeField(auto_now_add=True)

    # --- NEW/CHANGED FIELDS FOR ENCRYPTED FILE ---
    # This field will store the encrypted *bytes* of the file
    encrypted_attachment = models.BinaryField(blank=True, null=True)
    # This field stores the original file name (e.g., "cat.jpg")
    attachment_name = models.CharField(max_length=255, blank=True, null=True)
    
    @property
    def content(self) -> str:
        """
        This 'getter' decrypts the content when you access 'note.content'.
        """
        return decrypt_data(self.encrypted_content)

    @content.setter
    def content(self, value: str):
        """
        This 'setter' encrypts the content when you set 'note.content = ...'.
        """
        self.encrypted_content = encrypt_data(value)

    def __str__(self):
        return self.title

    # --- NEW METHODS FOR ENCRYPTED FILE ---

    def set_attachment(self, file_object):
        """
        Encrypts and sets the attachment from a file-like object.
        """
        if file_object:
            # Read the raw bytes from the uploaded file
            file_bytes = file_object.read()
            # Encrypt the bytes using the raw Fernet object
            self.encrypted_attachment = f.encrypt(file_bytes)
            # Store the original file name
            self.attachment_name = file_object.name
        else:
            self.encrypted_attachment = None
            self.attachment_name = None

    def get_attachment(self):
        """
        Returns the decrypted bytes and original file name.
        """
        if self.encrypted_attachment:
            try:
                decrypted_bytes = f.decrypt(self.encrypted_attachment)
                return decrypted_bytes, self.attachment_name
            except InvalidToken:
                return None, "Decryption Failed"
        return None, None

class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # --- The 'parent' field has been REMOVED ---

    def __str__(self):
        # --- Reverted __str__ method ---
        return f"Schedule for {self.title}"