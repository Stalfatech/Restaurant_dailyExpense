from django.contrib.messages import get_messages
from .models import Notification


class SaveMessagesMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        response = self.get_response(request)

        if request.user.is_authenticated:

            storage = get_messages(request)

            # copy messages without breaking template display
            message_list = [m for m in storage]

            for message in message_list:

                branch = None
                name = ""

                if request.user.user_type == 0:
                    name = request.user.name or "Admin"

                elif request.user.user_type == 1:
                    name = request.user.name
                    branch = request.user.branch

                elif request.user.user_type == 2:
                    name = request.user.name
                    branch = request.user.branch

                Notification.objects.get_or_create(
                    message=str(message),
                    tag=message.tags,
                    user=request.user,
                    branch=branch,
                    created_by_name=name
                )

        return response