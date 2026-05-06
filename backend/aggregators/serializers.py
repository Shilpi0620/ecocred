from rest_framework import serializers

from backend.aggregators.models import Aggregator, AggregatorCommission, PickupJob
from backend.waste.models import Material
from backend.waste.serializers import MaterialSerializer, SubmissionListSerializer


class AggregatorSerializer(serializers.ModelSerializer):
    accepted_materials = MaterialSerializer(many=True, read_only=True)
    accepted_material_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        source="accepted_materials",
        queryset=Material.objects.all(),
    )
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Aggregator
        fields = [
            "id",
            "username",
            "company_name",
            "address",
            "latitude",
            "longitude",
            "service_radius_km",
            "accepted_materials",
            "accepted_material_ids",
            "commission_rate_pct",
            "is_verified",
            "is_available",
            "rating",
            "total_kg_collected",
            "total_commission_earned",
        ]
        read_only_fields = [
            "is_verified",
            "rating",
            "total_kg_collected",
            "total_commission_earned",
        ]


class PickupJobSerializer(serializers.ModelSerializer):
    submission = SubmissionListSerializer(read_only=True)
    aggregator_name = serializers.CharField(source="aggregator.company_name", read_only=True)

    class Meta:
        model = PickupJob
        fields = [
            "id",
            "submission",
            "aggregator_name",
            "status",
            "distance_km",
            "commission_amount",
            "accepted_at",
            "collected_at",
            "forwarded_at",
            "notes",
            "created_at",
        ]
        read_only_fields = [
            "commission_amount",
            "accepted_at",
            "collected_at",
            "forwarded_at",
            "created_at",
        ]


class CommissionSerializer(serializers.ModelSerializer):
    job_id = serializers.IntegerField(source="job.id", read_only=True)
    material = serializers.CharField(source="job.submission.material.name", read_only=True)
    weight_kg = serializers.DecimalField(
        source="job.submission.weight_kg",
        max_digits=8,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = AggregatorCommission
        fields = ["id", "job_id", "material", "weight_kg", "amount", "status", "paid_at", "created_at"]


class AggregatorEarningsSummarySerializer(serializers.Serializer):
    total_earned = serializers.DecimalField(max_digits=12, decimal_places=2)
    this_month = serializers.DecimalField(max_digits=10, decimal_places=2)
    this_week = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_kg = serializers.DecimalField(max_digits=10, decimal_places=2)
    commission_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
