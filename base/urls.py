from django.urls import path
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from .views import *

urlpatterns = [

    path('login/',LoginPage,name = "login"),
    path('register/',RegisterUser,name = "register"),
    path('',home,name="home"),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('room/<str:pk>/',room,name="room"),
    path('create-room/',CreateRoom,name="create-room"),
    path('update-room<str:pk>/',UpdateRoom,name="update-room"),
    path('delete-room<str:pk>/',DeleteRoom,name="delete-room"),

]