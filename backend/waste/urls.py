from django.urls import path

from .views import (
    ManualVerifyView,
    MaterialListView,
    SubmissionDetailView,
    SubmissionListCreateView,
    VerificationLogView,
)


urlpatterns = [
    path("materials/", MaterialListView.as_view()),
    path("submissions/", SubmissionListCreateView.as_view()),
    path("submissions/<int:pk>/", SubmissionDetailView.as_view()),
    path("submissions/<int:pk>/verify/", ManualVerifyView.as_view()),
    path("submissions/<int:pk>/logs/", VerificationLogView.as_view()),
]
