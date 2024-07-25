# assistant/assistant_service.py
import json
import logging
import queue
import threading
from .models import AssistantThread
from typing_extensions import override
from django.conf import settings
from openai import OpenAI, AssistantEventHandler
from django.http import StreamingHttpResponse

logger = logging.getLogger(__name__)

def show_json(obj):
    logger.info(json.loads(obj.model_dump_json()))

class SousChefAssistant:
    def __init__(self, request):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.assistant_name = 'Sous Chef Assistant'
        self.model_id = 'gpt-4-turbo'
        self.instruction = 'You are a Sous Chef assistant. You help users with recipes and meal planning.'
        self.tools=[
            {
                "type":"function",
                "function":{
                    "name":"update_user_allergies",
                    "description":"Save the food allergies for the user in the backend database.",
                    "parameters":{
                        "type":"object",
                        "properties":{
                            "food_allergies":{
                                "type":"string",
                                "description":"A list of foods the user has specified they are allergic to."
                            },
                        },
                        "required":["food_allergies"]
                    }
                }
            }
        ]

        self.request = request
        self.user = request.user
        self.session = request.session
        self.assistant = self.get_or_create_assistant()
        self.thread = self.get_or_create_thread()

    def get_or_create_assistant(self):
        logger.info('get_or_create_assistant hit')
        assistant_thread, created = AssistantThread.objects.get_or_create(user=self.user)
        if 'assistant_id' in self.session:
            logger.info('assistant_id was found in session')
            return self.retrieve_assistant(self.session['assistant_id'])  
        elif assistant_thread.assistant_id:
            logger.info('assistant_id found in database')
            return self.retrieve_assistant(assistant_thread.assistant_id)            
        else:            
            return self.create_assistant()

    def retrieve_assistant(self, assistant_id):
        try:
            retrieved_assistant = self.client.beta.assistants.retrieve(assistant_id)
            self.session['assistant_id'] = assistant_id
            return retrieved_assistant
        except:
            logger.exception(f"An error occurred while retrieving assistant id ({assistant_id})")        
            return self.create_assistant()
    
    def create_assistant(self):
        logger.info('creating new assistant')
        assistant_thread = AssistantThread.objects.get(user=self.user) 
        new_assistant = self.client.beta.assistants.create(name=self.assistant_name, instructions=self.instruction, model=self.model_id, tools=self.tools)
        self.session['assistant_id'] = new_assistant.id
        assistant_thread.assistant_id = new_assistant.id
        assistant_thread.save()
        
    def get_or_create_thread(self):        
        logger.info('get_or_create_thread hit')
        assistant_thread = AssistantThread.objects.get(user=self.user)        
        if 'thread_id' in self.session:
            logger.info('thread_id was found in session')
            return self.retrieve_thread(self.session['thread_id'])
        elif assistant_thread.thread_id:
            logger.info('thread_id found in database')
            retrieved_thread = self.retrieve_thread(assistant_thread.thread_id)                        
            return retrieved_thread
        else:
            return self.create_thread()

    def retrieve_thread(self, thread_id):
        try:
            retrieved_thread = self.client.beta.threads.retrieve(thread_id)
            self.session['thread_id'] = thread_id
            return retrieved_thread
        except:
            logger.exception(f"An error occurred while retrieving thread id ({thread_id})")        
            return self.create_thread()   

    def create_thread(self):
        logger.info('creating new thread')
        assistant_thread = AssistantThread.objects.get(user=self.user)
        new_thread = self.client.beta.threads.create()
        self.session['thread_id'] = new_thread.id
        assistant_thread.thread_id = new_thread.id
        assistant_thread.save()
        return new_thread

    def add_message_to_thread(self, role, message):
        return self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role=role,
            content=message,            
        )

    def check_and_cancel_active_run(self):
        logger.info('check_and_cancel_active_run hit')
        runs = self.client.beta.threads.runs.list(thread_id=self.thread.id)
        if runs.data:
            for run in runs:
                # logger.info(f'status for run {run.id}: {run.status}')
                if run.status in ["queued", "in_progress"]:
                    logger.info(f'cancelling run {run.id}')       
                    self.client.beta.threads.runs.cancel(thread_id=self.thread.id, run_id=run.id)                    
    
    def get_previous_messages(self):
        logger.info('get_previous_messages hit')
        messages = self.client.beta.threads.messages.list(thread_id=self.thread.id, order="desc")
        previous_messages = []
        for message in messages.data:
            content = message.content[0].text.value
            role = message.role
            previous_messages.append({'content': content, 'role': role})
        return previous_messages
    
    def ask_assistant(self, user_message):
        delta_queue = queue.Queue()

        def event_stream():
            #logger.info('event_stream hit')
            event_handler = SousChefEventHandler(delta_queue, self)

            def run_assistant():
                logger.info('run_assistant hit')
                self.check_and_cancel_active_run()
                self.add_message_to_thread("user", user_message)
                logger.info('creating new run')
                with self.client.beta.threads.runs.stream(
                    thread_id=self.thread.id,
                    assistant_id=self.assistant.id,
                    event_handler=event_handler,
                ) as stream:
                    stream.until_done()
                logger.info('run_assistant completed')

            assistant_thread = threading.Thread(target=run_assistant)
            assistant_thread.start()

            while True:
                try:           
                    delta = delta_queue.get(timeout=1)
                    formatted_delta = delta.replace('\n', '\\n')
                    yield f"data: {formatted_delta}\n\n"
                except queue.Empty:
                    if not assistant_thread.is_alive():
                        break

        return StreamingHttpResponse(event_stream(), content_type='text/event-stream')
 
class SousChefEventHandler(AssistantEventHandler):
    def __init__(self, delta_queue, assistant):
        super().__init__()
        self.delta_queue = delta_queue
        self.assistant = assistant

    @override
    def on_text_created(self, text) -> None:
        #print(f"\nassistant > ", end="", flush=True)
        exit

    @override
    def on_text_delta(self, delta, snapshot):
        # print(delta.value, end="", flush=True)
        self.delta_queue.put(delta.value)
    
    @override
    def on_event(self, event):
      # Retrieve events that are denoted with 'requires_action'
      # since these will have our tool_calls    
      if event.event == 'thread.run.requires_action':
        run_id = event.data.id  # Retrieve the run ID from the event data
        # logger.info(event.data)
        self.handle_requires_action(event.data, run_id)
    
    def handle_requires_action(self, data, run_id):
      tool_outputs = []
        
      for tool in data.required_action.submit_tool_outputs.tool_calls:
        if tool.function.name == "update_user_allergies":
          logger.info('update_user_allergies requested!!')
          tool_outputs.append({"tool_call_id": tool.id, "output": "Pepsi"})
        
        # Submit all tool_outputs at the same time
        self.submit_tool_outputs(tool_outputs, run_id)
    
    def submit_tool_outputs(self, tool_outputs, run_id):
        logger.info('submit_tool_outputs hit')        
        with self.assistant.client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.assistant.thread.id,
            run_id=self.current_run.id,
            tool_outputs=tool_outputs,
            event_handler=SousChefEventHandler(self.delta_queue,self.assistant),
        ) as stream:
            stream.until_done()
        logger.info('submit_tool_outputs completed')