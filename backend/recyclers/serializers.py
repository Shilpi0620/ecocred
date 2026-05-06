from rest_framework import serializers

from backend.recyclers.models import IncomingShipment, MaterialInventory, ProcessingBatch, Recycler
from backend.waste.models import Material
from backend.waste.serializers import MaterialSerializer


class RecyclerSerializer(serializers.ModelSerializer):
    accepted_materials = MaterialSerializer(many=True, read_only=True)
    accepted_material_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        source="accepted_materials",
        queryset=Material.objects.all(),
    )
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Recycler
        fields = [
            "id",
            "username",
            "company_name",
            "license_number",
            "address",
            "accepted_materials",
            "accepted_material_ids",
            "is_verified",
            "total_kg_processed",
            "total_revenue",
        ]
        read_only_fields = ["is_verified", "total_kg_processed", "total_revenue"]


class InventorySerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source="material.name", read_only=True)
    material_icon = serializers.CharField(source="material.icon", read_only=True)
    material_slug = serializers.CharField(source="material.slug", read_only=True)
    cash_per_kg = serializers.DecimalField(
        source="material.cash_per_kg",
        max_digits=8,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = MaterialInventory
        fields = [
            "id",
            "material_name",
            "material_icon",
            "material_slug",
            "cash_per_kg",
            "quantity_kg",
            "last_updated",
        ]


class IncomingShipmentSerializer(serializers.ModelSerializer):
    aggregator_name = serializers.CharField(source="job.aggregator.company_name", read_only=True)
    material_name = serializers.CharField(source="job.submission.material.name", read_only=True)
    material_icon = serializers.CharField(source="job.submission.material.icon", read_only=True)

    class Meta:
        model = IncomingShipment
        fields = [
            "id",
            "aggregator_name",
            "material_name",
            "material_icon",
            "expected_weight_kg",
            "actual_weight_kg",
            "eta",
            "status",
            "received_at",
        ]
        read_only_fields = ["received_at"]


class ProcessingBatchSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source="material.name", read_only=True)
    yield_pct = serializers.FloatField(read_only=True)

    class Meta:
        model = ProcessingBatch
        fields = [
            "id",
            "material_name",
            "weight_in_kg",
            "weight_out_kg",
            "yield_pct",
            "stage",
            "revenue_generated",
            "user_credit_paid",
            "started_at",
            "completed_at",
        ]
        read_only_fields = ["yield_pct", "started_at"]


class RevenueSummarySerializer(serializers.Serializer):
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    this_month = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_kg_processed = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_user_credits_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    margin_pct = serializers.FloatField()
