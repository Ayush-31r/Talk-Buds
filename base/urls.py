from django.urls import path
from django.contrib import admin
from .views import *

urlpatterns = [

    path('login/',LoginPage,name = "login"),
    path('',home,name="home"),
    path('room/<str:pk>/',room,name="room"),
    path('create-room/',CreateRoom,name="create-room"),
    path('update-room<str:pk>/',UpdateRoom,name="update-room"),
    path('delete-room<str:pk>/',DeleteRoom,name="delete-room"),

]