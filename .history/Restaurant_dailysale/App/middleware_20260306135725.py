from django.contrib.messages import get_messages
from django.contrib import messages
from .models import Notification


class SaveMessagesMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        response = self.get_response(request)

        storage = get_messages(request)
        message_list = list(storage)

        # session flag storage
        if "saved_messages" not in request.session:
            request.session["saved_messages"] = []

        saved_messages = request.session["saved_messages"]

        if request.user.is_authenticated:

            for message in message_list:

                message_text = str(message)

                # prevent duplicate saving
                if message_text in saved_messages:
                    continue

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

                Notification.objects.create(
                    message=message_text,
                    tag=message.tags,
                    user=request.user,
                    branch=branch,
                    created_by_name=name
                )

                saved_messages.append(message_text)

        request.session["saved_messages"] = saved_messages

        # restore messages for template display
        for msg in message_list:
            messages.add_message(request, msg.level, msg.message, extra_tags=msg.tags)

        return response