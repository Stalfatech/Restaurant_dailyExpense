from django.contrib.messages import get_messages
from .models import Notification

class SaveMessagesMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        response = self.get_response(request)

        storage = get_messages(request)

        for message in storage:
            Notification.objects.create(
                message=str(message),
                tag=message.tags
            )

        # IMPORTANT: put messages back so templates can still display them
        storage.used = False

        return response