from django.urls import path

from .views import RewardsSummaryView, TransactionListView, WithdrawalListView, WithdrawalRequestView


urlpatterns = [
    path("transactions/", TransactionListView.as_view()),
    path("withdraw/", WithdrawalRequestView.as_view()),
    path("withdrawals/", WithdrawalListView.as_view()),
    path("summary/", RewardsSummaryView.as_view()),
]
