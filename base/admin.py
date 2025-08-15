from django.contrib import admin
from .models import User, Room, Topic, Message

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'is_staff')
    search_fields = ('username', 'email')

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'topic', 'host')
    search_fields = ('name', 'topic__name', 'host__username')
    list_filter = ('topic',)

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'user', 'created')
    search_fields = ('room__name', 'user__username', 'body')
    list_filter = ('room', 'created')
