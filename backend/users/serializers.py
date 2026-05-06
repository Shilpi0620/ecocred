from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from backend.users.models import RewardTier, User


class RewardTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardTier
        fields = [
            "id",
            "name",
            "min_points",
            "max_points",
            "cash_bonus_pct",
            "priority_collection",
            "dedicated_aggregator",
            "instant_payout",
            "description",
        ]


class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "total_points", "total_kg_recycled"]


class UserProfileSerializer(serializers.ModelSerializer):
    current_tier = RewardTierSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "role",
            "address",
            "latitude",
            "longitude",
            "wallet_balance",
            "total_points",
            "total_kg_recycled",
            "current_tier",
            "profile_photo",
            "date_joined",
        ]
        read_only_fields = [
            "id",
            "username",
            "role",
            "wallet_balance",
            "total_points",
            "total_kg_recycled",
            "date_joined",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
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
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
