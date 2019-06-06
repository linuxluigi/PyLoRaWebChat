from django.shortcuts import render

from .models import Node


def room(request):
    nodes: Node = Node.objects.all().order_by('nick')

    return render(request, 'chat/index.html', {
        "nodes": nodes
    })
