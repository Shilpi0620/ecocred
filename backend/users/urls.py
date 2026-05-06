from django.urls import path

from .views import (
    FCMTokenUpdateView,
    LeaderboardView,
    LoginView,
    ProfileView,
    RegisterView,
    TierListView,
    TokenRefreshView,
)


urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view()),
    path("profile/", ProfileView.as_view()),
    path("tiers/", TierListView.as_view()),
    path("leaderboard/", LeaderboardView.as_view()),
    path("fcm-token/", FCMTokenUpdateView.as_view()),
]
