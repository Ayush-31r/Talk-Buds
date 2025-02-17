from channels.generic.websocket import AsyncWebsocketConsumer
import json
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from .models import Room, message

User = get_user_model()
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"


        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        messages = await sync_to_async(lambda: list(
            message.objects.filter(room_id=self.room_id).values("user__username", "body", "created")
        ))()

        for msg in messages:
            await self.send(text_data=json.dumps({
                "user": msg["user__username"],
                "message": msg["body"],
                "timestamp": str(msg["created"])
            }))

    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )


    async def receive(self, text_data):
        data = json.loads(text_data)
        message_body = data.get("message")
        user_id = data.get("user_id")
        username = data.get("username")

        user = await sync_to_async(User.objects.get)(id=user_id)
        room = await sync_to_async(Room.objects.get)(id=self.room_id)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message_body,
                "user": user,
            }
        )

        message_obj = await sync_to_async(message.objects.create)(
            user=user, room=room, body=message_body
        )

        timestamp = message_obj.created.strftime('%Y-%m-%d %H:%M:%S')

        await self.channel_layer.group_send(
        self.room_group_name,
        {
            "type": "chat_message",
            "message": message_body,
            "user_id": user.id,
            "username": user.username,
            "timestamp": timestamp
        }
    )

    async def chat_message(self, event):
        """ Sends the message to all users in the room """
        await self.send(text_data=json.dumps({
            "user_id": event.get("user_id"),
            "username": event.get("username"),
            "message": event.get("message"),
            "timestamp": event.get("timestamp")
    }))



