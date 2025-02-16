from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]  # Get room ID
        self.room_group_name = f"chat_{self.room_id}"  # Use room ID

        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # async def receive(self, text_data):
    #     print("Raw text_data received:", text_data)  # Debugging log

    #     try:
    #         data = json.loads(text_data)  # Convert JSON string to dictionary
    #         print("Parsed data:", data)   # Debugging log

    #         user = data["username"]  # This is where the error happens
    #         message = data["message"]

    #         # Process the message...
        
    #     except KeyError as e:
    #         print(f"Missing key in WebSocket message: {e}")
    #     except json.JSONDecodeError as e:
    #         print(f"Error decoding JSON: {e}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]
        user = data["username"]

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "user": user,
            }
        )

    async def chat_message(self, event):
        message = event["message"]
        user = event["user"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "message": message,
            "user": user,
        }))
