from django.urls import path
from . import views

urlpatterns = [
    path('chatbot/', views.chatbot_response, name='chatbot_response'),
    path('history/', views.chat_history, name='chat_history'),
    path('conversations/', views.list_conversations, name='list_conversations'),
    path('conversations/<int:conv_id>/', views.delete_conversation, name='delete_conversation'),
]