# assistant/urls.py
from django.urls import path
from .views import chat_interface, ask_assistant, delete_thread

urlpatterns = [
    path('chat/', chat_interface, name='chat-interface'),
    path('ask/', ask_assistant, name='ask-assistant'),
    path('delete_thread/', delete_thread, name='delete-thread'),
]