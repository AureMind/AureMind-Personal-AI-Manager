from django.contrib import admin
from .models import Note, Task

class NoteAdmin(admin.ModelAdmin):
    # Show these fields in the list view
    list_display = ('title', 'user', 'created_at', 'attachment_name')
    
    # Do not show the encrypted fields in the admin edit form
    exclude = ('encrypted_content', 'encrypted_attachment')
    
    # Make 'content' property read-only in the admin
    readonly_fields = ('content_display',)

    def content_display(self, obj):
        # Show a placeholder instead of the decrypted content
        return "Content is encrypted and not visible in admin."
    content_display.short_description = "Note Content"

    # We must add 'content_display' to the fieldset
    # to make it appear in the admin.
    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'attachment_name', 'content_display')
        }),
    )
    
    # Make attachment_name readonly as well
    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields + ('attachment_name',)

admin.site.register(Note, NoteAdmin) # Register with our custom admin
admin.site.register(Task)