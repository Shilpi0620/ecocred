# ═══════════════════════════════════════════════════════════
# FILE 1: apps/rewards/webhook.py
# Paystack webhook — confirms when transfers actually land
# ═══════════════════════════════════════════════════════════

import hashlib
import hmac
import json

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone

from backend.rewards.models import WithdrawalRequest
from backend.notifications.tasks import send_push


@csrf_exempt
@require_POST
def paystack_webhook(request):
    """
    Paystack calls this URL when a transfer succeeds or fails.
    
    Add to ecocred/urls.py:
        path("webhooks/paystack/", paystack_webhook),
    
    Set in Paystack dashboard:
        Webhook URL: https://yourapi.com/webhooks/paystack/
    """
    # ── Verify signature ──
    paystack_signature = request.headers.get("X-Paystack-Signature", "")
    computed = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode("utf-8"),
        request.body,
        hashlib.sha512
    ).hexdigest()

    if not hmac.compare_digest(computed, paystack_signature):
        return HttpResponse("Invalid signature", status=401)

    # ── Parse event ──
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse("Invalid JSON", status=400)

    event     = payload.get("event")
    data      = payload.get("data", {})
    reference = data.get("reference", "")

    if event == "transfer.success":
        try:
            wr = WithdrawalRequest.objects.get(paystack_reference=reference)
            wr.status       = "paid"
            wr.processed_at = timezone.now()
            wr.save()

            send_push.delay(
                wr.user.id,
                "Payment Sent! 💵",
                f"₦{wr.amount:,.0f} has been sent to your {wr.bank_name} account."
            )
        except WithdrawalRequest.DoesNotExist:
            pass

    elif event == "transfer.failed":
        try:
            wr = WithdrawalRequest.objects.get(paystack_reference=reference)
            # Refund wallet
            wr.user.wallet_balance += wr.amount
            wr.user.save(update_fields=["wallet_balance"])
            wr.status = "rejected"
            wr.save()

            send_push.delay(
                wr.user.id,
                "Transfer Failed ⚠️",
                f"Your withdrawal of ₦{wr.amount:,.0f} failed. Your wallet has been refunded."
            )
        except WithdrawalRequest.DoesNotExist:
            pass

    elif event == "transfer.reversed":
        try:
            wr = WithdrawalRequest.objects.get(paystack_reference=reference)
            wr.user.wallet_balance += wr.amount
            wr.user.save(update_fields=["wallet_balance"])
            wr.status = "rejected"
            wr.save()
        except WithdrawalRequest.DoesNotExist:
            pass

    return HttpResponse("OK", status=200)


# ═══════════════════════════════════════════════════════════
# FILE 2: apps/users/admin.py
# Django admin customization
# ═══════════════════════════════════════════════════════════

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from backend.users.models import User, RewardTier


@admin.register(RewardTier)
class RewardTierAdmin(admin.ModelAdmin):
    list_display  = ["name", "min_points", "max_points", "cash_bonus_pct",
                     "priority_collection", "instant_payout"]
    ordering      = ["min_points"]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ["username", "email", "role", "total_points",
                     "wallet_balance", "current_tier", "is_active", "date_joined"]
    list_filter   = ["role", "current_tier", "is_active"]
    search_fields = ["username", "email", "phone"]
    ordering      = ["-date_joined"]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("EcoCred Profile", {
            "fields": (
                "role", "phone", "address", "latitude", "longitude",
                "wallet_balance", "total_points", "total_kg_recycled",
                "current_tier", "fcm_token"
            )
        }),
    )
    readonly_fields = ["wallet_balance", "total_points", "total_kg_recycled"]


# ═══════════════════════════════════════════════════════════
# FILE 3: apps/waste/admin.py
# ═══════════════════════════════════════════════════════════

from django.contrib import admin
from backend.waste.models import Material, WasteSubmission, VerificationLog


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display  = ["name", "slug", "icon", "points_per_kg", "cash_per_kg", "is_active"]
    list_editable = ["points_per_kg", "cash_per_kg", "is_active"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(WasteSubmission)
class WasteSubmissionAdmin(admin.ModelAdmin):
    list_display  = ["id", "user", "material", "weight_kg", "status",
                     "ml_confidence", "points_awarded", "cash_awarded", "created_at"]
    list_filter   = ["status", "material", "ml_verified", "manually_reviewed"]
    search_fields = ["user__username", "user__email"]
    ordering      = ["-created_at"]
    readonly_fields = [
        "ml_predicted_material", "ml_confidence", "ml_verified",
        "points_awarded", "cash_awarded", "base_points", "tier_bonus_pct"
    ]

    # Show manual review queue at the top
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        from django.db.models import Case, When, IntegerField
        return qs.annotate(
            review_order=Case(
                When(status="manual_review", then=0),
                default=1,
                output_field=IntegerField()
            )
        ).order_by("review_order", "-created_at")

    actions = ["approve_submissions", "reject_submissions"]

    def approve_submissions(self, request, queryset):
        from backend.waste.tasks import calculate_and_award_rewards
        count = 0
        for sub in queryset.filter(status="manual_review"):
            if not sub.ml_predicted_material:
                sub.ml_predicted_material = sub.material
                sub.save()
            calculate_and_award_rewards(sub.id, manual=True)
            count += 1
        self.message_user(request, f"Approved {count} submissions.")
    approve_submissions.short_description = "Approve selected submissions"

    def reject_submissions(self, request, queryset):
        updated = queryset.filter(status="manual_review").update(
            status="rejected", manually_reviewed=True, reviewed_by=request.user
        )
        self.message_user(request, f"Rejected {updated} submissions.")
    reject_submissions.short_description = "Reject selected submissions"


@admin.register(VerificationLog)
class VerificationLogAdmin(admin.ModelAdmin):
    list_display = ["submission", "predicted_label", "confidence_score",
                    "model_version", "processing_time_ms", "created_at"]
    list_filter  = ["model_version"]
    ordering     = ["-created_at"]


# ═══════════════════════════════════════════════════════════
# FILE 4: fixtures/initial_data.json
# Seed data — run: python manage.py loaddata initial_data
# ═══════════════════════════════════════════════════════════

FIXTURES_JSON = """
[
  {
    "model": "users.rewardtier",
    "pk": 1,
    "fields": {
      "name": "Bronze",
      "min_points": 0,
      "max_points": 249,
      "cash_bonus_pct": "0.00",
      "priority_collection": false,
      "dedicated_aggregator": false,
      "instant_payout": false,
      "description": "Standard rate. Basic collection priority."
    }
  },
  {
    "model": "users.rewardtier",
    "pk": 2,
    "fields": {
      "name": "Silver",
      "min_points": 250,
      "max_points": 499,
      "cash_bonus_pct": "5.00",
      "priority_collection": true,
      "dedicated_aggregator": false,
      "instant_payout": false,
      "description": "+5% cash bonus on every submission. Priority collection."
    }
  },
  {
    "model": "users.rewardtier",
    "pk": 3,
    "fields": {
      "name": "Gold",
      "min_points": 500,
      "max_points": 999,
      "cash_bonus_pct": "12.00",
      "priority_collection": true,
      "dedicated_aggregator": true,
      "instant_payout": false,
      "description": "+12% cash bonus. Dedicated aggregator assigned to you."
    }
  },
  {
    "model": "users.rewardtier",
    "pk": 4,
    "fields": {
      "name": "Platinum",
      "min_points": 1000,
      "max_points": null,
      "cash_bonus_pct": "20.00",
      "priority_collection": true,
      "dedicated_aggregator": true,
      "instant_payout": true,
      "description": "+20% cash bonus. Instant payouts. VIP support."
    }
  },
  {
    "model": "waste.material",
    "pk": 1,
    "fields": {
      "name": "Plastic",
      "slug": "plastic",
      "icon": "🧴",
      "points_per_kg": "2.50",
      "cash_per_kg": "25.00",
      "is_active": true
    }
  },
  {
    "model": "waste.material",
    "pk": 2,
    "fields": {
      "name": "Metal",
      "slug": "metal",
      "icon": "🔩",
      "points_per_kg": "8.00",
      "cash_per_kg": "80.00",
      "is_active": true
    }
  },
  {
    "model": "waste.material",
    "pk": 3,
    "fields": {
      "name": "Paper",
      "slug": "paper",
      "icon": "📄",
      "points_per_kg": "1.50",
      "cash_per_kg": "15.00",
      "is_active": true
    }
  },
  {
    "model": "waste.material",
    "pk": 4,
    "fields": {
      "name": "Glass",
      "slug": "glass",
      "icon": "🍾",
      "points_per_kg": "3.00",
      "cash_per_kg": "30.00",
      "is_active": true
    }
  },
  {
    "model": "waste.material",
    "pk": 5,
    "fields": {
      "name": "E-Waste",
      "slug": "ewaste",
      "icon": "💻",
      "points_per_kg": "15.00",
      "cash_per_kg": "150.00",
      "is_active": true
    }
  },
  {
    "model": "waste.material",
    "pk": 6,
    "fields": {
      "name": "Organic",
      "slug": "organic",
      "icon": "🌿",
      "points_per_kg": "1.00",
      "cash_per_kg": "10.00",
      "is_active": true
    }
  },
  {
    "model": "waste.material",
    "pk": 7,
    "fields": {
      "name": "Cardboard",
      "slug": "cardboard",
      "icon": "📦",
      "points_per_kg": "1.50",
      "cash_per_kg": "15.00",
      "is_active": true
    }
  }
]
"""

# Save to fixtures/initial_data.json
import os, json
fixtures_dir = os.path.join(os.path.dirname(__file__), "..", "fixtures")
os.makedirs(fixtures_dir, exist_ok=True)
with open(os.path.join(fixtures_dir, "initial_data.json"), "w") as f:
    f.write(FIXTURES_JSON)
