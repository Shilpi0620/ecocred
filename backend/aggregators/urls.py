from django.urls import path

from .views import (
    AcceptJobView,
    AggregatorEarningsSummaryView,
    AggregatorProfileView,
    CollectJobView,
    CommissionListView,
    ForwardToRecyclerView,
    PickupJobListView,
)


urlpatterns = [
    path("profile/", AggregatorProfileView.as_view()),
    path("jobs/", PickupJobListView.as_view()),
    path("jobs/<int:pk>/accept/", AcceptJobView.as_view()),
    path("jobs/<int:pk>/collect/", CollectJobView.as_view()),
    path("jobs/<int:pk>/forward/", ForwardToRecyclerView.as_view()),
    path("commissions/", CommissionListView.as_view()),
    path("earnings/summary/", AggregatorEarningsSummaryView.as_view()),
]
