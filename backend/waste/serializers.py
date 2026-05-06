from rest_framework import serializers

from backend.waste.models import Material, VerificationLog, WasteSubmission


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ["id", "name", "slug", "icon", "points_per_kg", "cash_per_kg", "is_active"]


class VerificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationLog
        fields = [
            "id",
            "model_version",
            "predicted_label",
            "confidence_score",
            "processing_time_ms",
            "raw_output",
            "created_at",
        ]


class SubmissionListSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source="material.name", read_only=True)
    material_icon = serializers.CharField(source="material.icon", read_only=True)
    material_slug = serializers.CharField(source="material.slug", read_only=True)

    class Meta:
        model = WasteSubmission
        fields = [
            "id",
            "material_name",
            "material_icon",
            "material_slug",
            "weight_kg",
            "status",
            "points_awarded",
            "cash_awarded",
            "ml_confidence",
            "ml_verified",
            "created_at",
        ]


class SubmissionDetailSerializer(serializers.ModelSerializer):
    material = MaterialSerializer(read_only=True)
    material_id = serializers.PrimaryKeyRelatedField(
        queryset=Material.objects.filter(is_active=True),
        source="material",
        write_only=True,
    )
    ml_material_name = serializers.CharField(source="ml_predicted_material.name", read_only=True)
    logs = VerificationLogSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source="user.username", read_only=True)
    user_address = serializers.CharField(source="user.address", read_only=True)

    class Meta:
        model = WasteSubmission
        fields = [
            "id",
            "user_name",
            "user_address",
            "material",
            "material_id",
            "image",
            "weight_kg",
            "notes",
            "preferred_pickup_date",
            "status",
            "ml_material_name",
            "ml_confidence",
            "ml_verified",
            "manually_reviewed",
            "base_points",
            "tier_bonus_pct",
            "points_awarded",
            "cash_awarded",
            "logs",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "status",
            "ml_confidence",
            "ml_verified",
            "manually_reviewed",
            "base_points",
            "tier_bonus_pct",
            "points_awarded",
            "cash_awarded",
            "logs",
            "user_name",
            "user_address",
            "created_at",
            "updated_at",
        ]

    def validate_weight_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError("Weight must be greater than 0.")
        if value > 1000:
            raise serializers.ValidationError("Weight cannot exceed 1000 kg per submission.")
        return value
