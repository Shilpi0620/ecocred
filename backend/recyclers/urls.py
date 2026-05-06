from django.urls import path

from .views import (
    BatchListView,
    ConfirmShipmentView,
    InventoryListView,
    RecyclerProfileView,
    RevenueSummaryView,
    ShipmentListView,
    UpdateBatchView,
)


urlpatterns = [
    path("profile/", RecyclerProfileView.as_view()),
    path("inventory/", InventoryListView.as_view()),
    path("shipments/", ShipmentListView.as_view()),
    path("shipments/<int:pk>/confirm/", ConfirmShipmentView.as_view()),
    path("batches/", BatchListView.as_view()),
    path("batches/<int:pk>/update/", UpdateBatchView.as_view()),
    path("revenue/summary/", RevenueSummaryView.as_view()),
]
