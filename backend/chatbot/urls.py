from django.urls import path
from . import views
from .rag import views as rag_views

urlpatterns = [
    path('chatbot/', views.chatbot_response, name='chatbot_response'),
    path('history/', views.chat_history, name='chat_history'),
    path('conversations/', views.list_conversations, name='list_conversations'),
    path('conversations/<int:conv_id>/', views.delete_conversation, name='delete_conversation'),
    path('progress/students/', views.student_progress, name='student_progress'),
    path('rag/upload/', rag_views.upload_document, name='rag_upload_document'),
    path('rag/ask/', rag_views.ask_question, name='rag_ask_question'),
]
