from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from .models import *
from .forms import *



# Create your views here.

def LoginPage(request):
    
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')


        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request, 'User does not exist')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username OR password does not exist')

    context = {'page' : page}
    return render(request, 'base/login_register.html', context)

def logoutUser(request):
    logout(request)
    return redirect('home')


def RegisterUser(request):
    form = MyUserCreationForm()
    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=True)
            user.username = user.username.lower()
            user.save()
            login(request,user)
            return redirect('home')
        
        else:
            messages.error(request,"Error has occured during registration, Try again")
    return render(request,'base/login_register.html',{'form':form})

def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )

    topics = Topic.objects.all()
    room_count = rooms.count()
    chats = message.objects.all()


    context = {'rooms' : rooms,'topics' : topics,'room_count':room_count, 'chats' : chats}
    return render(request,'base/home.html',context)

def room(request,pk):
    room = Room.objects.get(id=pk)
    chats = room.message_set.all().order_by('-created')
    participants = room.participants.all()
    if request.method == 'POST':
        chat = message.objects.create(
            user = request.user,
            room=room,
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)
    
    context = {'room' : room , 'chats' : chats, 'participants' : participants,}
    return render(request,'base/room.html',context)


def profile(request,pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    chats = user.message_set.all().order_by('-created')
    topics = Topic.objects.all()
    context = {'user':user,'rooms':rooms,'chats':chats,'topics':topics}
    return render(request,'base/profile.html',context)

def Topics(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q)
    )

    topics = Topic.objects.all()
    room_count = rooms.count()


    context = {'rooms' : rooms,'topics' : topics,'room_count':room_count}
    return render(request,'base/topics.html',context)

def Activity(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )

    topics = Topic.objects.all()
    chats = message.objects.all()


    context = {'rooms' : rooms,'topics' : topics, 'chats' : chats}
    return render(request,'base/activity.html',context)


@login_required(login_url='login')
def CreateRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic,created = Topic.objects.get_or_create(name = topic_name)
        form = RoomForm(request.POST)
        Room.objects.create(
            host = request.user,
            topic = topic,
            name = request.POST.get('name'),
            description = request.POST.get('description')
        )
        return redirect('home')
    context = {'form' : form, 'topics':topics}
    return render(request,'base/room_form.html',context)

@login_required(login_url='login')
def UpdateRoom(request,pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic,created = Topic.objects.get_or_create(name = topic_name)
        room.name = request.POST.get('name')
        room.description = request.POST.get('description')
        room.topic = topic
        room.save()
        return redirect('home')
    context = {'form' : form,'topics':topics, 'room':room}
    return render(request,'base/room_form.html',context)

@login_required(login_url='login')
def DeleteRoom(request,pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse('You are not allowed here !!')

    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request,'base/delete.html',{'obj' :room})

@login_required(login_url='login')
def DeleteChat(request,pk):
    chat = message.objects.get(id=pk)

    if request.user != chat.user:
        return HttpResponse('You are not allowed here !!')

    if request.method == 'POST':
        chat.delete()
        return redirect('home')
    return render(request,'base/delete.html',{'obj' : chat})

@login_required(login_url='login')
def UpdateUser(request):
    user = request.user
    form = UserForm(instance=user)
    if request.method == 'POST':
        form = UserForm(request.POST,request.FILES,instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile' ,pk = user.id)
    context = {'user':user,'form':form}
    return render(request,'base/UpdateUser.html',context)