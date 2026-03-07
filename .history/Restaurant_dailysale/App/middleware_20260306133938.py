from django.contrib.messages import get_messages
from .models import Notification

class SaveMessagesMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        response = self.get_response(request)

        storage = get_messages(request)

        if request.user.is_authenticated:

            for message in storage:

                branch = None
                name = ""

                if request.user.user_type == 0:  # Admin
                    name = request.user.name or "Admin"

                elif request.user.user_type == 1:  # Manager
                    name = request.user.name
                    branch = request.user.branch

                Notification.objects.create(
                    message=str(message),
                    tag=message.tags,
                    user=request.user,
                    branch=branch,
                    created_by_name=name
                )

        return response