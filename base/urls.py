from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,  # POST: get access/refresh tokens
    TokenRefreshView,     # POST: refresh access token
    TokenBlacklistView,   # POST: blacklist a refresh token
)
from . import views

urlpatterns = [
    # Auth Pages
    path('login/', views.login_page, name="login"),
    path('register/', views.RegisterUser, name="register"),
    path('logout/', views.logoutUser, name="logout"),

    # Main Pages
    path('', views.home, name="home"),
    path('room/<str:pk>/', views.room, name="room"),
    path('profile/<str:pk>/', views.profile, name="profile"),
    path('topics/', views.Topics, name="topics"),
    path('activity/', views.Activity, name="activity"),

    # Room CRUD
    path('create-room/', views.CreateRoom, name="create-room"),
    path('update-room/<str:pk>/', views.UpdateRoom, name="update-room"),
    path('delete-room/<str:pk>/', views.DeleteRoom, name="delete-room"),

    # Chat CRUD
    path('delete-message/<str:pk>/', views.DeleteChat, name="delete-message"),

    # User Profile
    path('update-user/', views.UpdateUser, name="update-user"),

    # API Endpoints for scaling chat (used by WebSocket + caching)
    path('api/messages/<str:room_id>/', views.api_get_recent_messages, name="api-get-recent-messages"),

    # JWT Auth for API/WebSocket use
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
]
