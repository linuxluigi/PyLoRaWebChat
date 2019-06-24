from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from .models import Node


def room(request):
    if request.user.is_superuser:
        nodes: Node = Node.objects.all().order_by("nick")

        response = render_to_response("chat/index.html", {"nodes": nodes})

    else:
        response = render_to_response("chat/403.html", {})
        response.status_code = 403

    return response
