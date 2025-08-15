from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    name = models.CharField(max_length=200, null=True, db_index=True)
    email = models.EmailField(unique=True, null=True, db_index=True)
    bio = models.TextField(null=True, blank=True)
    avatar = models.ImageField(null=True, default="avatar.svg")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["name"]),
        ]


class Topic(models.Model):
    name = models.CharField(max_length=200, unique=True, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
        ]


class Room(models.Model):
    host = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="hosted_rooms", db_index=True
    )
    topic = models.ForeignKey(
        Topic, on_delete=models.SET_NULL, null=True, related_name="rooms", db_index=True
    )
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(null=True, blank=True)
    participants = models.ManyToManyField(
        User, related_name="participating_rooms", blank=True
    )
    updated = models.DateTimeField(auto_now=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-updated", "-created"]
        indexes = [
            models.Index(fields=["updated"]),
            models.Index(fields=["created"]),
            models.Index(fields=["topic", "updated"]),
        ]

    def __str__(self):
        return self.name


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages", db_index=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="messages", db_index=True)
    body = models.TextField()
    updated = models.DateTimeField(auto_now=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-updated", "-created"]
        indexes = [
            models.Index(fields=["updated"]),
            models.Index(fields=["created"]),
            models.Index(fields=["room", "created"]),
        ]

    def __str__(self):
        return self.body[:50]
