from django.db import models
from django.contrib.auth.models import User

class AssistantThread(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    assistant_id = models.CharField(max_length=255, null=True, blank=True)
    thread_id = models.CharField(max_length=255, null=True, blank=True)
