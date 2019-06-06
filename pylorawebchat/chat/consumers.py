import json

from channels.generic.websocket import AsyncWebsocketConsumer

from config.settings.base import CHANNEL_CHAT_ROOM, CHANNEL_CHAT_GROUP
from .models import Message, Node


class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = CHANNEL_CHAT_ROOM
        self.room_group_name = CHANNEL_CHAT_GROUP

    async def connect(self):
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        if 'node_pk' in event['message'].keys():

            message: str = event['message']['message']
            node_pk = int(event['message']['node_pk'])

            message_model: Message = Message(
                node=Node.objects.get(pk=node_pk),
                message=message,
                message_type='o',
                instant_send=False
            )

            message_model.save()

            # Send message to WebSocket
            await self.send(text_data=json.dumps({
                'message': message_model.to_json(created=True)
            }))
        else:
            # Send message to WebSocket
            await self.send(text_data=json.dumps({
                'message': event['message']
            }))
