from django.contrib import admin

from .models import Node, Message


class MessageInline(admin.StackedInline):
    model = Message
    extra = 3


class NodeAdmin(admin.ModelAdmin):
    fields = ['address', 'nick']
    inlines = [MessageInline]


admin.site.register(Node, NodeAdmin)
admin.site.register(Message)
