from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from channels.db import database_sync_to_async
from .models import Room, Message, User
import logging
import redis.asyncio as redis
import os
import pickle  # serialize Python objects for Redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
MESSAGE_HISTORY_LIMIT = 50
MESSAGE_CACHE_TTL = 60 * 5  # 5 minutes


class ChatConsumer(AsyncWebsocketConsumer):

    async def _get_redis(self):
        """Get a Redis connection."""
        if not hasattr(self, "_redis"):
            self._redis = await redis.from_url(REDIS_URL, decode_responses=False)
        return self._redis

    @database_sync_to_async
    def _aget_room(self, room_id: int) -> Room:
        return Room.objects.get(id=room_id)

    @database_sync_to_async
    def _acreate_message(self, user: User, room: Room, body: str) -> Message:
        return Message.objects.create(user=user, room=room, body=body)

    @database_sync_to_async
    def _aadd_participant(self, room: Room, user: User):
        room.participants.add(user)

    @database_sync_to_async
    def _afetch_messages_db(self, limit: int = 50, before_id: int | None = None):
        qs = (
            Message.objects.filter(room_id=self.room_id)
            .select_related("user")
            .order_by("-id")
        )
        if before_id:
            qs = qs.filter(id__lt=before_id)
        items = list(qs[:limit])
        items.reverse()
        return items

    async def _afetch_messages(self, limit: int = 50, before_id: int | None = None):
        """Fetch from Redis cache first, fallback to DB."""
        redis = await self._get_redis()
        cache_key = f"room:{self.room_id}:history:{before_id or 'latest'}"
        cached = await redis.get(cache_key)
        if cached:
            try:
                return pickle.loads(cached)
            except Exception as e:
                logger.warning(f"Cache decode failed: {e}")

        # Fallback to DB
        msgs = await self._afetch_messages_db(limit, before_id)
        await redis.setex(cache_key, MESSAGE_CACHE_TTL, pickle.dumps(msgs))
        return msgs

    def _serialize_message(self, m: Message) -> dict:
        return {
            "message_id": m.id,
            "user_id": m.user.id if m.user else None,
            "username": m.user.username if m.user else "Unknown",
            "message": m.body,
            "timestamp": self._iso(m.created),
        }

    def _iso(self, dt):
        if not dt:
            return None
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt.isoformat()

    async def send_json(self, data: dict):
        await self.send(text_data=json.dumps(data))

    async def connect(self):
        self.user = self.scope.get("user")
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"

        if not self.user or not self.user.is_authenticated:
            await self.close(code=401)
            return

        try:
            self.room = await self._aget_room(self.room_id)
        except ObjectDoesNotExist:
            await self.close(code=404)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        history = await self._afetch_messages(limit=MESSAGE_HISTORY_LIMIT)
        await self.send_json({
            "type": "message_history",
            "direction": "latest",
            "messages": [self._serialize_message(m) for m in history],
        })

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "presence_event",
                "event": "user_joined",
                "user_id": self.user.id,
                "username": self.user.username,
            },
        )

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "presence_event",
                    "event": "user_left",
                    "user_id": getattr(self.user, "id", None),
                    "username": getattr(self.user, "username", None),
                },
            )
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or "{}")
        except json.JSONDecodeError:
            await self.send_json({"type": "error", "message": "Invalid JSON"})
            return

        if not self.user or not self.user.is_authenticated:
            await self.send_json({"type": "error", "message": "Authentication required"})
            return

        evt_type = data.get("type")

        if evt_type == "chat_message":
            body = (data.get("message") or "").strip()
            if not body:
                return
            if len(body) > 1000:
                await self.send_json({"type": "error", "message": "Message too long"})
                return

            msg_obj = await self._acreate_message(self.user, self.room, body)
            await self._aadd_participant(self.room, self.user)

            # Invalidate Redis cache for latest messages
            redis = await self._get_redis()
            await redis.delete(f"room:{self.room_id}:history:latest")

            payload = {
                "type": "chat_message",
                "message": body,
                "timestamp": self._iso(msg_obj.created),
                "user_id": self.user.id,
                "username": self.user.username,
                "message_id": msg_obj.id,
            }
            await self.channel_layer.group_send(self.room_group_name, payload)

        elif evt_type == "load_more":
            before_id = data.get("before_id")
            if before_id is not None and not isinstance(before_id, int):
                return
            older = await self._afetch_messages(limit=MESSAGE_HISTORY_LIMIT, before_id=before_id)
            await self.send_json({
                "type": "message_history",
                "direction": "older",
                "messages": [self._serialize_message(m) for m in older],
            })

        elif evt_type == "typing":
            is_typing = bool(data.get("is_typing"))
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_event",
                    "user_id": self.user.id,
                    "username": self.user.username,
                    "is_typing": is_typing,
                },
            )

        else:
            await self.send_json({"type": "error", "message": f"Unknown event type: {evt_type}"})

    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        user_id = event['user_id']

        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
            'user_id': user_id
        }))

    async def presence_event(self, event):
        await self.send_json({
            "type": "presence",
            "event": event.get("event"),
            "user_id": event.get("user_id"),
            "username": event.get("username"),
        })

    async def typing_event(self, event):
        await self.send_json({
            "type": "typing",
            "user_id": event.get("user_id"),
            "username": event.get("username"),
            "is_typing": event.get("is_typing", False),
        })
