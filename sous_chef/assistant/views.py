import logging
from django.shortcuts import render, redirect
from .assistant_service import SousChefAssistant
from .models import AssistantThread
from django.conf import settings

logger = logging.getLogger(__name__)

def chat_interface(request):
    assistant = SousChefAssistant(request)
    previous_messages = assistant.get_previous_messages()
    context = {
        'previous_messages': previous_messages,
        'debug': settings.DEBUG,
    }
    return render(request, 'assistant/chat.html', context)

def ask_assistant(request):
    user_message = request.GET.get('message', '')
    assistant = SousChefAssistant(request)

    return assistant.ask_assistant(user_message=user_message)

def create_new_thread(request):
    assistant = SousChefAssistant(request)

def delete_thread(request):
    logger.info('delete_thread hit!')
    thread_id = request.session['thread_id']
    logger.info(f'thread_id: {thread_id}')
    
    assistant = SousChefAssistant(request)    
    response = assistant.client.beta.threads.delete(thread_id)
    logger.info(response)
    
    if response.deleted:
        logger.info('delete the previous thread_id from the session')
        
        try:
            del request.session['thread_id']
        except KeyError:
            pass        

        try:
            assistant_thread = AssistantThread.objects.get(user=request.user)
            assistant_thread.thread_id = None
            logger.info('thread_id set to None on the backend database')
        except AssistantThread.DoesNotExist:
            logger.exception('The assistant_thread was not found in the backend database')
    
    return redirect('chat-interface')

def delete_assistant(request):
    logger.info('delete_assistant hit!')
    
    assistant = SousChefAssistant(request)    
    response = assistant.client.beta.assistants.delete(assistant_id=assistant.assistant.id)
    logger.info(response)
    
    if response.deleted:
        logger.info('delete the assistant_id and thread_id from the session')
        
        try:
            del request.session['thread_id']
            del request.session['assistant_id']
        except KeyError:
            pass
        
        try:
            assistant_thread = AssistantThread.objects.get(user=request.user)
            assistant_thread.delete()
            logger.info('assistant_thread deleted from the backend database')
        except AssistantThread.DoesNotExist:
            logger.info('assistant_thread not found in the backend database')
    
    return redirect('chat-interface')
