import json
import redis.asyncio as redis
from asgiref.sync import async_to_sync
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db import IntegrityError
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Room, Topic, Message, User
from .forms import MyUserCreationForm, RoomForm, UserForm

# Redis connection settings
REDIS_URL = "redis://localhost:6379"
REDIS_ROOM_CACHE_PREFIX = "room_messages:"
MAX_CACHED_MESSAGES = 50


def get_redis():
    """Return a Redis connection."""
    return redis.from_url(REDIS_URL, decode_responses=True)


@require_http_methods(["GET", "POST"])
def login_page(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""

        if not email or not password:
            messages.error(request, "Please enter both email and password.")
            return redirect("login")

        user = authenticate(request, email=email, password=password)

        if user:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, "base/login_register.html", {"page": "login"})


def logoutUser(request):
    logout(request)
    return redirect('home')


@require_http_methods(["GET", "POST"])
def RegisterUser(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.username = user.username.lower()
                user.save()

                login(request, user)
                messages.success(request, "Account created successfully!")
                return redirect('home')

            except IntegrityError:
                messages.error(request, "A user with this email already exists.")
            
        else:
            messages.error(request, "Please correct the errors below.")
    
    return render(request, 'base/login_register.html', {'form': form})


def home(request):
    q = request.GET.get('q') or ''

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )

    topics = Topic.objects.all()
    room_count = rooms.count()

    context = {
        'rooms': rooms,
        'topics': topics,
        'room_count': room_count
    }
    return render(request, 'base/home.html', context)


@login_required(login_url='login')
def room(request, pk):
    room = get_object_or_404(Room, id=pk)
    r = get_redis()

    cached_messages = async_to_sync(r.lrange)(f"{REDIS_ROOM_CACHE_PREFIX}{pk}", -MAX_CACHED_MESSAGES, -1)
    if cached_messages:
        chats = [json.loads(msg) for msg in cached_messages]
    else:
        chats_qs = room.messages.all().order_by('-created')[:MAX_CACHED_MESSAGES]
        chats = [
            {"user": m.user.username, "body": m.body, "created": m.created.isoformat()}
            for m in chats_qs
        ]

    participants = room.participants.all()

    if request.method == 'POST':
        body = request.POST.get('body')
        if body:
            chat = Message.objects.create(user=request.user, room=room, body=body)
            room.participants.add(request.user)

            payload = {
                "user": request.user.username,
                "body": chat.body,
                "created": chat.created.isoformat(),
                "room_id": room.id
            }

            async_to_sync(r.rpush)(f"{REDIS_ROOM_CACHE_PREFIX}{pk}", json.dumps(payload))
            async_to_sync(r.ltrim)(f"{REDIS_ROOM_CACHE_PREFIX}{pk}", -MAX_CACHED_MESSAGES, -1)
            async_to_sync(r.publish)(f"room_{pk}", json.dumps(payload))

            return redirect('room', pk=room.id)
    
    context = {
        'room': room,
        'chats': chats,
        'participants': participants,
        'user_id': request.user.id,
        'username': request.user.username
    }
    return render(request, 'base/room.html', context)


def profile(request, pk):
    user = get_object_or_404(User, id=pk)
    rooms = user.rooms.all()
    chats = user.messages.all().order_by('-created')
    topics = Topic.objects.all()
    context = {'user': user, 'rooms': rooms, 'chats': chats, 'topics': topics}
    return render(request, 'base/profile.html', context)


def Topics(request):
    q = request.GET.get('q') or ''
    rooms = Room.objects.filter(Q(topic__name__icontains=q))
    topics = Topic.objects.all()
    context = {'rooms': rooms, 'topics': topics, 'room_count': rooms.count()}
    return render(request, 'base/topics.html', context)


def Activity(request):
    q = request.GET.get('q') or ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )
    topics = Topic.objects.all()
    chats = Message.objects.all()
    context = {'rooms': rooms, 'topics': topics, 'chats': chats}
    return render(request, 'base/activity.html', context)


@login_required(login_url='login')
def CreateRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, _ = Topic.objects.get_or_create(name=topic_name)
        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description')
        )
        return redirect('home')
    return render(request, 'base/room_form.html', {'form': form, 'topics': topics})


@login_required(login_url='login')
def UpdateRoom(request, pk):
    room = get_object_or_404(Room, id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, _ = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.description = request.POST.get('description')
        room.topic = topic
        room.save()
        return redirect('home')
    return render(request, 'base/room_form.html', {'form': form, 'topics': topics, 'room': room})


@login_required(login_url='login')
def DeleteRoom(request, pk):
    room = get_object_or_404(Room, id=pk)
    if request.user != room.host:
        return HttpResponse('You are not allowed here !!')

    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': room})


@login_required(login_url='login')
def DeleteChat(request, pk):
    chat = get_object_or_404(Message, id=pk)
    if request.user != chat.user:
        return HttpResponse('You are not allowed here !!')

    if request.method == 'POST':
        chat.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': chat})


@login_required(login_url='login')
def UpdateUser(request):
    user = request.user
    form = UserForm(instance=user)
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile', pk=user.id)
    return render(request, 'base/UpdateUser.html', {'user': user, 'form': form})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_recent_messages(request, room_id):
    """Return last 50 messages for a room, preferring Redis cache."""
    r = get_redis()
    cached_messages = async_to_sync(r.lrange)(f"{REDIS_ROOM_CACHE_PREFIX}{room_id}", -MAX_CACHED_MESSAGES, -1)

    if cached_messages:
        messages_list = [json.loads(msg) for msg in cached_messages]
    else:
        room = get_object_or_404(Room, id=room_id)
        chats_qs = room.messages.all().order_by('-created')[:MAX_CACHED_MESSAGES]
        messages_list = [
            {"user": m.user.username, "body": m.body, "created": m.created.isoformat()}
            for m in chats_qs
        ]

    return JsonResponse(messages_list, safe=False)
