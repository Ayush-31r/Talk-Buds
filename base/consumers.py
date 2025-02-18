from channels.generic.websocket import AsyncWebsocketConsumer
import json
# from asgiref.sync import database_sync_to_async
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from .models import Room, message, User

# User = get_user_model()
import logging

logger = logging.getLogger(__name__)
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room = await database_sync_to_async(Room.objects.get)(id=self.room_id)
        self.room_group_name = f"chat_{self.room_id}"


        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        messages = await database_sync_to_async(lambda: list(
            message.objects.filter(room_id=self.room_id)
            .select_related("user")  # Ensure user data is fetched efficiently
        ))()

        # Send previous messages to the connected user in the correct format
        for msg in messages:
            await self.send(text_data=json.dumps({
                "user_id": msg.user.id if msg.user else None,  # Ensure no crash if user is null
                "username": msg.user.username if msg.user else "Unknown",  # Fix username issue
                "message": msg.body,
                "timestamp": msg.created.strftime('%Y-%m-%d %H:%M:%S')
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

        user = await database_sync_to_async(User.objects.get)(id=user_id)
        room = await database_sync_to_async(Room.objects.get)(id=self.room_id)

        # await self.channel_layer.group_send(
        #     self.room_group_name,
        #     {
        #         "type": "chat_message",
        #         "message": message_body,
        #         "user": user,
        #     }
        # )

        message_obj = await database_sync_to_async(message.objects.create)(
            user=user, room=room, body=message_body
        )

        timestamp = message_obj.created.strftime('%Y-%m-%d %H:%M:%S')

        await self.channel_layer.group_send(
        self.room_group_name,
        {
            "type": "chat_message",
            "message": message_body,
            "user_id": user.id,
            "username": username,
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



