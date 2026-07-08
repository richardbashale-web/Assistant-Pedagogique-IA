from django.contrib import admin
from .models import ChatMessage

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'sender', 'text', 'timestamp')
    list_filter = ('sender', 'user')
    search_fields = ('text',)
