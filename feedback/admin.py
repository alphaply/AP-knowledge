from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'contact_person', 'created_at', 'is_handled')
    list_filter = ('is_handled', 'created_at')
    readonly_fields = ('ip_address', 'created_at')