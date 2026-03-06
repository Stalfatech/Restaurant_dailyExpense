from django.contrib.messages import get_messages
from django.contrib import messages
from .models import Notification


class SaveMessagesMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        response = self.get_response(request)

        storage = get_messages(request)
        message_list = list(storage)   # store messages

        if request.user.is_authenticated:

            for message in message_list:

                branch = None
                name = ""

                if request.user.user_type == 0:  # Admin
                    name = request.user.name or "Admin"

                elif request.user.user_type == 1:  # Manager
                    name = request.user.name
                    branch = request.user.branch

                elif request.user.user_type == 2:  # Staff
                    name = request.user.name
                    branch = request.user.branch

                Notification.objects.create(
                    message=str(message),
                    tag=message.tags,
                    user=request.user,
                    branch=branch,
                    created_by_name=name
                )

        # re-add messages so templates can show them
        for msg in message_list:
            messages.add_message(request, msg.level, msg.message, extra_tags=msg.tags)

        return response