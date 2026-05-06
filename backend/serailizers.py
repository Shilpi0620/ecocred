# ═══════════════════════════════════════════════════════════
# EcoCred — All Serializers
# Split across apps but shown together for clarity
# ═══════════════════════════════════════════════════════════


# ─────────────────────────────────────────────────────────
# apps/users/serializers.py
# ─────────────────────────────────────────────────────────
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from apps.users.models import User, RewardTier


class RewardTierSerializer(serializers.ModelSerializer):
    class Meta:
        model  = RewardTier
        fields = [
            "id", "name", "min_points", "max_points",
            "cash_bonus_pct", "priority_collection",
            "dedicated_aggregator", "instant_payout", "description"
        ]


class UserPublicSerializer(serializers.ModelSerializer):
    """Minimal user info for leaderboard / other users."""
    class Meta:
        model  = User
        fields = ["id", "username", "total_points", "total_kg_recycled"]


class UserProfileSerializer(serializers.ModelSerializer):
    """Full profile for authenticated user."""
    current_tier = RewardTierSerializer(read_only=True)

    class Meta:
        model  = User
        fields = [
            "id", "username", "email", "phone", "role",
            "address", "latitude", "longitude",
            "wallet_balance", "total_points", "total_kg_recycled",
            "current_tier", "profile_photo", "date_joined"
        ]
        read_only_fields = [
            "id", "username", "role", "wallet_balance",
            "total_points", "total_kg_recycled", "date_joined"
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password         = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ["username", "email", "password", "confirm_password", "phone", "role"]

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def validate_role(self, value):
        allowed = ["user", "aggregator", "recycler"]
        if value not in allowed:
            raise serializers.ValidationError(f"Role must be one of: {allowed}")
        return value

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # Auto-assign Bronze tier
        from apps.users.models import RewardTier
        bronze = RewardTier.objects.filter(min_points=0).first()
        if bronze:
            user.current_tier = bronze
            user.save(update_fields=["current_tier"])

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data["username"], password=data["password"])
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account has been disabled.")
        data["user"] = user
        return data


def get_tokens_for_user(user):
    """Return JWT access + refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access":  str(refresh.access_token),
    }


# ─────────────────────────────────────────────────────────
# apps/waste/serializers.py
# ─────────────────────────────────────────────────────────
from rest_framework import serializers
from apps.waste.models import Material, WasteSubmission, VerificationLog


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Material
        fields = ["id", "name", "slug", "icon", "points_per_kg", "cash_per_kg", "is_active"]


class VerificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model  = VerificationLog
        fields = [
            "id", "model_version", "predicted_label",
            "confidence_score", "processing_time_ms",
            "raw_output", "created_at"
        ]


class SubmissionListSerializer(serializers.ModelSerializer):
    """Compact serializer for list views."""
    material_name = serializers.CharField(source="material.name", read_only=True)
    material_icon = serializers.CharField(source="material.icon", read_only=True)
    material_slug = serializers.CharField(source="material.slug", read_only=True)

    class Meta:
        model  = WasteSubmission
        fields = [
            "id", "material_name", "material_icon", "material_slug",
            "weight_kg", "status", "points_awarded", "cash_awarded",
            "ml_confidence", "ml_verified", "created_at"
        ]


class SubmissionDetailSerializer(serializers.ModelSerializer):
    """Full detail including ML predictions."""
    material         = MaterialSerializer(read_only=True)
    material_id      = serializers.PrimaryKeyRelatedField(
        queryset=Material.objects.filter(is_active=True),
        source="material", write_only=True
    )
    ml_material_name = serializers.CharField(
        source="ml_predicted_material.name", read_only=True
    )
    logs             = VerificationLogSerializer(many=True, read_only=True)
    user_name        = serializers.CharField(source="user.username", read_only=True)
    user_address     = serializers.CharField(source="user.address", read_only=True)

    class Meta:
        model  = WasteSubmission
        fields = [
            "id", "user_name", "user_address",
            "material", "material_id", "image",
            "weight_kg", "notes", "preferred_pickup_date",
            "status",
            # ML fields
            "ml_material_name", "ml_confidence", "ml_verified",
            "manually_reviewed",
            # Rewards
            "base_points", "tier_bonus_pct", "points_awarded", "cash_awarded",
            # Logs
            "logs",
            "created_at", "updated_at"
        ]
        read_only_fields = [
            "status", "ml_confidence", "ml_verified", "manually_reviewed",
            "base_points", "tier_bonus_pct", "points_awarded", "cash_awarded",
            "logs", "user_name", "user_address", "created_at", "updated_at"
        ]

    def validate_weight_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError("Weight must be greater than 0.")
        if value > 1000:
            raise serializers.ValidationError("Weight cannot exceed 1000 kg per submission.")
        return value


# ─────────────────────────────────────────────────────────
# apps/rewards/serializers.py
# ─────────────────────────────────────────────────────────
from rest_framework import serializers
from apps.rewards.models import Transaction, WithdrawalRequest
from apps.users.serializers import RewardTierSerializer


class TransactionSerializer(serializers.ModelSerializer):
    submission_id = serializers.IntegerField(source="submission.id", read_only=True, allow_null=True)

    class Meta:
        model  = Transaction
        fields = [
            "id", "transaction_type", "points", "amount",
            "description", "submission_id", "created_at"
        ]


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model  = WithdrawalRequest
        fields = [
            "id", "amount", "bank_name", "account_number",
            "account_name", "status", "paystack_reference",
            "processed_at", "created_at"
        ]
        read_only_fields = ["status", "paystack_reference", "processed_at", "created_at"]

    def validate_amount(self, value):
        if value < 1000:
            raise serializers.ValidationError("Minimum withdrawal is ₦1,000.")
        return value

    def validate(self, data):
        user = self.context["request"].user
        if float(user.wallet_balance) < float(data["amount"]):
            raise serializers.ValidationError({"amount": "Insufficient wallet balance."})
        return data


class RewardsSummarySerializer(serializers.Serializer):
    """Summary stats for the user's rewards dashboard."""
    total_points      = serializers.IntegerField()
    wallet_balance    = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_kg_recycled = serializers.DecimalField(max_digits=10, decimal_places=2)
    points_this_week  = serializers.IntegerField()
    cash_this_week    = serializers.DecimalField(max_digits=10, decimal_places=2)
    points_this_month = serializers.IntegerField()
    cash_this_month   = serializers.DecimalField(max_digits=10, decimal_places=2)
    current_tier      = RewardTierSerializer(allow_null=True)
    next_tier         = RewardTierSerializer(allow_null=True)
    points_to_next    = serializers.IntegerField(allow_null=True)


# ─────────────────────────────────────────────────────────
# apps/aggregators/serializers.py
# ─────────────────────────────────────────────────────────
from rest_framework import serializers
from apps.aggregators.models import Aggregator, PickupJob, AggregatorCommission
from apps.waste.serializers import MaterialSerializer, SubmissionListSerializer


class AggregatorSerializer(serializers.ModelSerializer):
    accepted_materials = MaterialSerializer(many=True, read_only=True)
    accepted_material_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, source="accepted_materials",
        queryset=__import__("apps.waste.models", fromlist=["Material"]).Material.objects.all()
    )
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model  = Aggregator
        fields = [
            "id", "username", "company_name", "address",
            "latitude", "longitude", "service_radius_km",
            "accepted_materials", "accepted_material_ids",
            "commission_rate_pct", "is_verified", "is_available",
            "rating", "total_kg_collected", "total_commission_earned"
        ]
        read_only_fields = [
            "is_verified", "rating",
            "total_kg_collected", "total_commission_earned"
        ]


class PickupJobSerializer(serializers.ModelSerializer):
    submission     = SubmissionListSerializer(read_only=True)
    aggregator_name = serializers.CharField(source="aggregator.company_name", read_only=True)

    class Meta:
        model  = PickupJob
        fields = [
            "id", "submission", "aggregator_name",
            "status", "distance_km", "commission_amount",
            "accepted_at", "collected_at", "forwarded_at",
            "notes", "created_at"
        ]
        read_only_fields = [
            "commission_amount", "accepted_at",
            "collected_at", "forwarded_at", "created_at"
        ]


class CommissionSerializer(serializers.ModelSerializer):
    job_id       = serializers.IntegerField(source="job.id", read_only=True)
    material     = serializers.CharField(source="job.submission.material.name", read_only=True)
    weight_kg    = serializers.DecimalField(
        source="job.submission.weight_kg",
        max_digits=8, decimal_places=2, read_only=True
    )

    class Meta:
        model  = AggregatorCommission
        fields = ["id", "job_id", "material", "weight_kg", "amount", "status", "paid_at", "created_at"]


class AggregatorEarningsSummarySerializer(serializers.Serializer):
    total_earned  = serializers.DecimalField(max_digits=12, decimal_places=2)
    this_month    = serializers.DecimalField(max_digits=10, decimal_places=2)
    this_week     = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending       = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_kg      = serializers.DecimalField(max_digits=10, decimal_places=2)
    commission_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


# ─────────────────────────────────────────────────────────
# apps/recyclers/serializers.py
# ─────────────────────────────────────────────────────────
from rest_framework import serializers
from apps.recyclers.models import (
    Recycler, MaterialInventory,
    IncomingShipment, ProcessingBatch
)
from apps.waste.serializers import MaterialSerializer


class RecyclerSerializer(serializers.ModelSerializer):
    accepted_materials    = MaterialSerializer(many=True, read_only=True)
    accepted_material_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, source="accepted_materials",
        queryset=__import__("apps.waste.models", fromlist=["Material"]).Material.objects.all()
    )
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model  = Recycler
        fields = [
            "id", "username", "company_name", "license_number",
            "address", "accepted_materials", "accepted_material_ids",
            "is_verified", "total_kg_processed", "total_revenue"
        ]
        read_only_fields = ["is_verified", "total_kg_processed", "total_revenue"]


class InventorySerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source="material.name", read_only=True)
    material_icon = serializers.CharField(source="material.icon", read_only=True)
    material_slug = serializers.CharField(source="material.slug", read_only=True)
    cash_per_kg   = serializers.DecimalField(
        source="material.cash_per_kg",
        max_digits=8, decimal_places=2, read_only=True
    )

    class Meta:
        model  = MaterialInventory
        fields = [
            "id", "material_name", "material_icon", "material_slug",
            "cash_per_kg", "quantity_kg", "last_updated"
        ]


class IncomingShipmentSerializer(serializers.ModelSerializer):
    aggregator_name  = serializers.CharField(source="job.aggregator.company_name", read_only=True)
    material_name    = serializers.CharField(source="job.submission.material.name", read_only=True)
    material_icon    = serializers.CharField(source="job.submission.material.icon", read_only=True)

    class Meta:
        model  = IncomingShipment
        fields = [
            "id", "aggregator_name", "material_name", "material_icon",
            "expected_weight_kg", "actual_weight_kg",
            "eta", "status", "received_at"
        ]
        read_only_fields = ["received_at"]


class ProcessingBatchSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source="material.name", read_only=True)
    yield_pct     = serializers.FloatField(read_only=True)

    class Meta:
        model  = ProcessingBatch
        fields = [
            "id", "material_name", "weight_in_kg", "weight_out_kg",
            "yield_pct", "stage", "revenue_generated",
            "user_credit_paid", "started_at", "completed_at"
        ]
        read_only_fields = ["yield_pct", "started_at"]


class RevenueSummarySerializer(serializers.Serializer):
    total_revenue         = serializers.DecimalField(max_digits=14, decimal_places=2)
    this_month            = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_kg_processed    = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_user_credits_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    margin_pct            = serializers.FloatField()