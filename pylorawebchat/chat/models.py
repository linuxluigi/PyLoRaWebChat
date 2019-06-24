from django.db import models
from django.db.models.signals import post_save, post_delete, ModelSignal
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class Node(models.Model):
    address = models.CharField(max_length=4, unique=True)

    nick = models.CharField(max_length=255, blank=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{}: {}".format(self.address, self.nick)

    def get_all_messages(self):
        return Message.objects.filter(node=self).order_by("timestamp")

    def to_json(self, created: bool = False):

        try:
            Node.objects.get(pk=self.pk)
            delete: bool = False
        except Node.DoesNotExist:
            delete: bool = True

        return {
            "model": "node",
            "id": self.pk,
            "nick": self.nick,
            "address": self.address,
            "first_seen": self.first_seen.strftime("%Y-%m-%d %H:%M"),
            "last_seen": self.last_seen.strftime("%Y-%m-%d %H:%M"),
            "delete": delete,
            "created": created,
        }


class Message(models.Model):
    MESSAGE_TYPE = (("i", "incoming"), ("o", "outgoing"))
    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    message = models.CharField(max_length=250)
    timestamp = models.DateTimeField(auto_now_add=True)
    message_type = models.CharField(max_length=1, choices=MESSAGE_TYPE)
    instant_send = models.BooleanField(default=True)

    def __str__(self):
        return "{} {} {}".format(self.message_type, self.node.nick, self.message)

    def to_json(self, created: bool = False):

        try:
            Message.objects.get(pk=self.pk)
            delete: bool = False
        except Message.DoesNotExist:
            delete: bool = True

        return {
            "model": "message",
            "id": self.pk,
            "node_id": self.node.pk,
            "node_nick": self.node.nick,
            "node_address": self.node.address,
            "message": self.message,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M"),
            "message_type": self.message_type,
            "delete": delete,
            "created": created,
        }


@receiver(post_delete, sender=Message)
@receiver(post_delete, sender=Node)
@receiver(post_save, sender=Message)
@receiver(post_save, sender=Node)
def after_save_instance_handler(sender, **kwargs: ModelSignal):
    if "created" in kwargs.keys():
        created: bool = kwargs["created"]
    else:
        created: bool = False

    if isinstance(kwargs["instance"], Message):
        message: Message = kwargs["instance"]

        if message.instant_send:
            async_to_sync(get_channel_layer().group_send)(
                "chat_group",
                {"type": "chat_message", "message": message.to_json(created=created)},
            )

    if isinstance(kwargs["instance"], Node):
        node_update: Node = kwargs["instance"]

        async_to_sync(get_channel_layer().group_send)(
            "chat_group",
            {"type": "chat_message", "message": node_update.to_json(created=created)},
        )
