from rest_framework import serializers

from backend.rewards.models import Transaction, WithdrawalRequest
from backend.users.serializers import RewardTierSerializer


class TransactionSerializer(serializers.ModelSerializer):
    submission_id = serializers.IntegerField(source="submission.id", read_only=True, allow_null=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "transaction_type",
            "points",
            "amount",
            "description",
            "submission_id",
            "created_at",
        ]


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalRequest
        fields = [
            "id",
            "amount",
            "bank_name",
            "account_number",
            "account_name",
            "status",
            "paystack_reference",
            "processed_at",
            "created_at",
        ]
        read_only_fields = ["status", "paystack_reference", "processed_at", "created_at"]

    def validate_amount(self, value):
        if value < 1000:
            raise serializers.ValidationError("Minimum withdrawal is 1000.")
        return value

    def validate(self, data):
        user = self.context["request"].user
        if float(user.wallet_balance) < float(data["amount"]):
            raise serializers.ValidationError({"amount": "Insufficient wallet balance."})
        return data


class RewardsSummarySerializer(serializers.Serializer):
    total_points = serializers.IntegerField()
    wallet_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_kg_recycled = serializers.DecimalField(max_digits=10, decimal_places=2)
    points_this_week = serializers.IntegerField()
    cash_this_week = serializers.DecimalField(max_digits=10, decimal_places=2)
    points_this_month = serializers.IntegerField()
    cash_this_month = serializers.DecimalField(max_digits=10, decimal_places=2)
    current_tier = RewardTierSerializer(allow_null=True)
    next_tier = RewardTierSerializer(allow_null=True)
    points_to_next = serializers.IntegerField(allow_null=True)
