import logging
import queue
import threading
from django.shortcuts import render, redirect
from django.http import JsonResponse, StreamingHttpResponse
from .assistant_service import SousChefAssistant, SousChefEventHandler
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
    delta_queue = queue.Queue()

    def event_stream():
        event_handler = SousChefEventHandler(delta_queue)

        def run_assistant():
            logger.info('run_assistant hit')
            assistant.check_and_cancel_active_run()
            assistant.add_message_to_thread("user", user_message)
            logger.info('creating new run')
            with assistant.client.beta.threads.runs.stream(
                thread_id=assistant.thread.id,
                assistant_id=assistant.assistant.id,
                event_handler=event_handler,
            ) as stream:
                stream.until_done()
            logger.info('run_assistant completed')

        assistant_thread = threading.Thread(target=run_assistant)
        assistant_thread.start()

        while True:
            try:           
                delta = delta_queue.get(timeout=1)
                # if '\n' in delta:
                    # logger.info("\\n detected in event_stream!")
                # logger.info(f"Streaming delta: {delta}")
                formatted_delta = delta.replace('\n', '\\n')
                yield f"data: {formatted_delta}\n\n"
            except queue.Empty:
                if not assistant_thread.is_alive():
                    break

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

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
        
        # Delete the thread_id from the backend database
        try:
            assistant_thread = AssistantThread.objects.get(thread_id=thread_id)
            assistant_thread.delete()
            logger.info('thread_id deleted from the backend database')
        except AssistantThread.DoesNotExist:
            logger.info('thread_id not found in the backend database')
    
    return redirect('chat-interface')
