# ═══════════════════════════════════════════════════════════
# EcoCred — All Views
# ═══════════════════════════════════════════════════════════


# ─────────────────────────────────────────────────────────
# apps/users/views.py
# ─────────────────────────────────────────────────────────
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from backend.users.models import User, RewardTier
from backend.users.serializers import (
    RegisterSerializer, LoginSerializer, UserProfileSerializer,
    RewardTierSerializer, UserPublicSerializer, get_tokens_for_user
)


def backend_home(request):
    return JsonResponse({
        "status": "ok",
        "message": "EcoCred backend is running.",
    })


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return Response({
            **tokens,
            "user": UserProfileSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        tokens = get_tokens_for_user(user)
        return Response({
            **tokens,
            "user": UserProfileSerializer(user).data
        })


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class   = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class FCMTokenUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get("fcm_token", "")
        request.user.fcm_token = token
        request.user.save(update_fields=["fcm_token"])
        return Response({"status": "updated"})


class TierListView(generics.ListAPIView):
    serializer_class   = RewardTierSerializer
    permission_classes = [IsAuthenticated]
    queryset           = RewardTier.objects.all().order_by("min_points")


class LeaderboardView(generics.ListAPIView):
    serializer_class   = UserPublicSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(
            role="user", is_active=True
        ).order_by("-total_points")[:20]


# ─────────────────────────────────────────────────────────
# apps/waste/views.py
# ─────────────────────────────────────────────────────────
from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend

from backend.waste.models import Material, WasteSubmission, VerificationLog
from backend.waste.serializers import (
    MaterialSerializer, SubmissionListSerializer,
    SubmissionDetailSerializer, VerificationLogSerializer
)
from backend.waste.tasks import process_ml_verification, calculate_and_award_rewards


DEFAULT_MATERIALS = [
    {"name": "Plastic Bottles", "slug": "plastic", "icon": "PL", "points_per_kg": "120", "cash_per_kg": "80"},
    {"name": "Aluminium Cans", "slug": "aluminium", "icon": "AL", "points_per_kg": "180", "cash_per_kg": "140"},
    {"name": "Cardboard", "slug": "cardboard", "icon": "CB", "points_per_kg": "90", "cash_per_kg": "60"},
    {"name": "Glass", "slug": "glass", "icon": "GL", "points_per_kg": "70", "cash_per_kg": "40"},
]


def ensure_default_materials():
    if Material.objects.exists():
        return

    for item in DEFAULT_MATERIALS:
        Material.objects.get_or_create(slug=item["slug"], defaults=item)


class MaterialListView(generics.ListAPIView):
    serializer_class   = MaterialSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        ensure_default_materials()
        return Material.objects.filter(is_active=True).order_by("name")


class SubmissionListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = ["status", "material"]
    ordering_fields    = ["created_at", "weight_kg"]
    ordering           = ["-created_at"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SubmissionDetailSerializer
        return SubmissionListSerializer

    def get_queryset(self):
        return WasteSubmission.objects.filter(
            user=self.request.user
        ).select_related("material", "ml_predicted_material")

    def perform_create(self, serializer):
        submission = serializer.save(user=self.request.user, status="pending")
        # Try async ML verification; fall back to manual review in local dev.
        try:
            process_ml_verification.delay(submission.id)
        except Exception:
            submission.status = "manual_review"
            submission.save(update_fields=["status"])


class SubmissionDetailView(generics.RetrieveAPIView):
    serializer_class   = SubmissionDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WasteSubmission.objects.filter(user=self.request.user)


class ManualVerifyView(APIView):
    """Admin manually approves or rejects low-confidence submissions."""
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        try:
            sub = WasteSubmission.objects.get(pk=pk, status="manual_review")
        except WasteSubmission.DoesNotExist:
            return Response({"error": "Submission not found or not in manual_review state."}, status=404)

        action = request.data.get("action")
        if action not in ("approve", "reject"):
            return Response({"error": "action must be 'approve' or 'reject'"}, status=400)

        if action == "approve":
            # Use ML-predicted material or fall back to user-selected
            if not sub.ml_predicted_material:
                sub.ml_predicted_material = sub.material
            calculate_and_award_rewards(sub.id, manual=True)
        else:
            sub.status = "rejected"
            sub.manually_reviewed = True
            sub.reviewed_by = request.user
            sub.save()
            from backend.notifications.tasks import send_push
            send_push.delay(
                sub.user.id,
                "Submission Update",
                "Your submission was reviewed and could not be verified. Please resubmit with a clearer photo."
            )

        return Response({"status": sub.status})


class VerificationLogView(generics.ListAPIView):
    serializer_class   = VerificationLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return VerificationLog.objects.filter(
            submission__user=self.request.user,
            submission__id=self.kwargs["pk"]
        )


# ─────────────────────────────────────────────────────────
# apps/rewards/views.py
# ─────────────────────────────────────────────────────────
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
from decimal import Decimal

from backend.rewards.models import Transaction, WithdrawalRequest
from backend.rewards.serializers import (
    TransactionSerializer, WithdrawalRequestSerializer,
    RewardsSummarySerializer
)
from backend.rewards.paystack import initiate_transfer
from backend.users.models import RewardTier


class TransactionListView(generics.ListAPIView):
    serializer_class   = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Transaction.objects.filter(
            user=self.request.user
        ).order_by("-created_at")
        tx_type = self.request.query_params.get("type")
        if tx_type:
            qs = qs.filter(transaction_type=tx_type)
        return qs


class WithdrawalRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WithdrawalRequestSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user   = request.user
        amount = Decimal(str(serializer.validated_data["amount"]))

        # Deduct from wallet and create request atomically
        from django.db import transaction as dbt
        with dbt.atomic():
            user.wallet_balance -= amount
            user.save(update_fields=["wallet_balance"])

            wr = serializer.save(user=user)

            # Try Paystack transfer
            bank_codes = {
                "First Bank": "011", "GTBank": "058",
                "Access Bank": "044", "Zenith Bank": "057", "UBA": "033"
            }
            bank_code = request.data.get("bank_code") or bank_codes.get(wr.bank_name, "011")

            if settings.PAYSTACK_SECRET_KEY:
                try:
                    result = initiate_transfer(
                        amount_naira=float(amount),
                        account_number=wr.account_number,
                        bank_code=bank_code,
                        name=wr.account_name,
                        reason=f"EcoCred withdrawal #{wr.id}",
                    )
                except Exception:
                    result = {"status": False}
            else:
                result = {
                    "status": True,
                    "data": {
                        "reference": f"DEV-WD-{wr.id}",
                    },
                }

            if result.get("status"):
                wr.paystack_reference = result["data"].get("reference", "")
                wr.status = "approved"
                wr.save()

                Transaction.objects.create(
                    user=user, transaction_type="cash_withdrawn",
                    amount=-amount,
                    description=f"Withdrawal to {wr.bank_name} {wr.account_number}"
                )
                return Response({
                    "status": "success",
                    "reference": wr.paystack_reference,
                    "amount": str(amount)
                })
            else:
                # Rollback wallet
                user.wallet_balance += amount
                user.save(update_fields=["wallet_balance"])
                wr.status = "rejected"
                wr.save()
                return Response(
                    {"error": "Transfer failed. Please try again."},
                    status=status.HTTP_502_BAD_GATEWAY
                )


class WithdrawalListView(generics.ListAPIView):
    serializer_class   = WithdrawalRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WithdrawalRequest.objects.filter(
            user=self.request.user
        ).order_by("-created_at")


class RewardsSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        now  = timezone.now()
        week_ago  = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        txns_week = Transaction.objects.filter(
            user=user, created_at__gte=week_ago, transaction_type="points_earned"
        )
        txns_month = Transaction.objects.filter(
            user=user, created_at__gte=month_ago, transaction_type="points_earned"
        )

        pts_week  = txns_week.aggregate(t=Sum("points"))["t"] or 0
        cash_week = txns_week.aggregate(t=Sum("amount"))["t"] or 0
        pts_month  = txns_month.aggregate(t=Sum("points"))["t"] or 0
        cash_month = txns_month.aggregate(t=Sum("amount"))["t"] or 0

        # Next tier
        next_tier = RewardTier.objects.filter(
            min_points__gt=user.total_points
        ).order_by("min_points").first()
        points_to_next = (next_tier.min_points - user.total_points) if next_tier else None

        data = {
            "total_points":      user.total_points,
            "wallet_balance":    user.wallet_balance,
            "total_kg_recycled": user.total_kg_recycled,
            "points_this_week":  pts_week,
            "cash_this_week":    cash_week,
            "points_this_month": pts_month,
            "cash_this_month":   cash_month,
            "current_tier":      user.current_tier,
            "next_tier":         next_tier,
            "points_to_next":    points_to_next,
        }
        serializer = RewardsSummarySerializer(data)
        return Response(serializer.data)


# ─────────────────────────────────────────────────────────
# apps/aggregators/views.py
# ─────────────────────────────────────────────────────────
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta

from backend.aggregators.models import Aggregator, PickupJob, AggregatorCommission
from backend.aggregators.serializers import (
    AggregatorSerializer, PickupJobSerializer,
    CommissionSerializer, AggregatorEarningsSummarySerializer
)


class IsAggregator(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == "aggregator"


class AggregatorProfileView(generics.RetrieveUpdateAPIView):
    serializer_class   = AggregatorSerializer
    permission_classes = [IsAggregator]

    def get_object(self):
        profile, _ = Aggregator.objects.get_or_create(
            user=self.request.user,
            defaults={
                "company_name": f"{self.request.user.username} Aggregator",
                "address": self.request.user.address or "Update your business address",
            },
        )
        return profile


class PickupJobListView(generics.ListAPIView):
    serializer_class   = PickupJobSerializer
    permission_classes = [IsAggregator]

    def get_queryset(self):
        qs = PickupJob.objects.filter(
            aggregator__user=self.request.user
        ).select_related(
            "submission__user", "submission__material", "aggregator"
        ).order_by("-created_at")

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class AcceptJobView(APIView):
    permission_classes = [IsAggregator]

    def patch(self, request, pk):
        try:
            job = PickupJob.objects.get(pk=pk, aggregator__user=request.user, status="pending")
        except PickupJob.DoesNotExist:
            return Response({"error": "Job not found or already accepted."}, status=404)

        job.status      = "accepted"
        job.accepted_at = timezone.now()
        job.save()

        # Notify user
        from backend.notifications.tasks import send_push
        send_push.delay(
            job.submission.user.id,
            "Pickup Accepted! 🚛",
            f"Your {job.submission.material.name} pickup has been accepted. Coming soon!"
        )
        return Response(PickupJobSerializer(job).data)


class CollectJobView(APIView):
    permission_classes = [IsAggregator]

    def patch(self, request, pk):
        try:
            job = PickupJob.objects.get(pk=pk, aggregator__user=request.user, status="accepted")
        except PickupJob.DoesNotExist:
            return Response({"error": "Job not found or not in accepted state."}, status=404)

        job.status       = "collected"
        job.collected_at = timezone.now()
        job.save()

        job.submission.status = "collected"
        job.submission.save(update_fields=["status"])

        return Response(PickupJobSerializer(job).data)


class ForwardToRecyclerView(APIView):
    permission_classes = [IsAggregator]

    def patch(self, request, pk):
        from backend.recyclers.models import Recycler
        from backend.recyclers.tasks import create_incoming_shipment
        from backend.aggregators.models import AggregatorCommission
        from decimal import Decimal
        from django.db import transaction as dbt

        try:
            job = PickupJob.objects.get(pk=pk, aggregator__user=request.user, status="collected")
        except PickupJob.DoesNotExist:
            return Response({"error": "Job not found or not collected yet."}, status=404)

        recycler_id = request.data.get("recycler_id")
        if not recycler_id:
            return Response({"error": "recycler_id is required."}, status=400)

        try:
            recycler = Recycler.objects.get(id=recycler_id, is_verified=True)
        except Recycler.DoesNotExist:
            return Response({"error": "Recycler not found."}, status=404)

        with dbt.atomic():
            job.status       = "forwarded"
            job.forwarded_at = timezone.now()
            job.save()

            # Calculate commission
            mat = job.submission.material
            cash_value = float(mat.cash_per_kg) * float(job.submission.weight_kg)
            commission = Decimal(str(cash_value * float(job.aggregator.commission_rate_pct) / 100))
            job.commission_amount = commission
            job.save(update_fields=["commission_amount"])

            AggregatorCommission.objects.create(
                aggregator=job.aggregator, job=job, amount=commission
            )

            agg = job.aggregator
            agg.total_kg_collected    += job.submission.weight_kg
            agg.total_commission_earned += commission
            agg.save()

        # Create shipment async
        create_incoming_shipment.delay(job.id, recycler.id)

        return Response({
            "status": "forwarded",
            "commission": str(commission),
            "recycler": recycler.company_name
        })


class CommissionListView(generics.ListAPIView):
    serializer_class   = CommissionSerializer
    permission_classes = [IsAggregator]

    def get_queryset(self):
        return AggregatorCommission.objects.filter(
            aggregator__user=self.request.user
        ).order_by("-created_at")


class AggregatorEarningsSummaryView(APIView):
    permission_classes = [IsAggregator]

    def get(self, request):
        agg, _ = Aggregator.objects.get_or_create(
            user=request.user,
            defaults={
                "company_name": f"{request.user.username} Aggregator",
                "address": request.user.address or "Update your business address",
            },
        )
        now  = timezone.now()
        week_ago  = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        commissions = AggregatorCommission.objects.filter(aggregator=agg)
        data = {
            "total_earned":   agg.total_commission_earned,
            "this_month":     commissions.filter(created_at__gte=month_ago).aggregate(t=Sum("amount"))["t"] or 0,
            "this_week":      commissions.filter(created_at__gte=week_ago).aggregate(t=Sum("amount"))["t"] or 0,
            "pending":        commissions.filter(status="pending").aggregate(t=Sum("amount"))["t"] or 0,
            "total_kg":       agg.total_kg_collected,
            "commission_rate": agg.commission_rate_pct,
        }
        serializer = AggregatorEarningsSummarySerializer(data)
        return Response(serializer.data)


# ─────────────────────────────────────────────────────────
# apps/recyclers/views.py
# ─────────────────────────────────────────────────────────
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction as dbt
from django.db.models import Sum
from decimal import Decimal

from backend.recyclers.models import (
    Recycler, MaterialInventory,
    IncomingShipment, ProcessingBatch
)
from backend.recyclers.serializers import (
    RecyclerSerializer, InventorySerializer,
    IncomingShipmentSerializer, ProcessingBatchSerializer,
    RevenueSummarySerializer
)


class IsRecycler(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == "recycler"


class RecyclerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class   = RecyclerSerializer
    permission_classes = [IsRecycler]

    def get_object(self):
        profile, _ = Recycler.objects.get_or_create(
            user=self.request.user,
            defaults={
                "company_name": f"{self.request.user.username} Recycler",
                "license_number": f"PENDING-{self.request.user.id}",
                "address": self.request.user.address or "Update your facility address",
            },
        )
        return profile


class InventoryListView(generics.ListAPIView):
    serializer_class   = InventorySerializer
    permission_classes = [IsRecycler]

    def get_queryset(self):
        return MaterialInventory.objects.filter(
            recycler__user=self.request.user
        ).select_related("material").order_by("-quantity_kg")


class ShipmentListView(generics.ListAPIView):
    serializer_class   = IncomingShipmentSerializer
    permission_classes = [IsRecycler]

    def get_queryset(self):
        qs = IncomingShipment.objects.filter(
            recycler__user=self.request.user
        ).select_related(
            "job__aggregator", "job__submission__material"
        ).order_by("-id")

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class ConfirmShipmentView(APIView):
    permission_classes = [IsRecycler]

    def patch(self, request, pk):
        try:
            shipment = IncomingShipment.objects.get(
                pk=pk, recycler__user=request.user
            )
        except IncomingShipment.DoesNotExist:
            return Response({"error": "Shipment not found."}, status=404)

        if shipment.status == "received":
            return Response({"error": "Shipment already confirmed."}, status=400)

        actual_weight = request.data.get("actual_weight_kg")
        if not actual_weight:
            return Response({"error": "actual_weight_kg is required."}, status=400)

        with dbt.atomic():
            shipment.status          = "received"
            shipment.actual_weight_kg = Decimal(str(actual_weight))
            shipment.received_at     = timezone.now()
            shipment.save()

            # Update inventory
            material = shipment.job.submission.material
            inv, _   = MaterialInventory.objects.get_or_create(
                recycler=shipment.recycler,
                material=material,
                defaults={"quantity_kg": 0}
            )
            inv.quantity_kg += Decimal(str(actual_weight))
            inv.save()

            # Final submission status
            shipment.job.submission.status = "recycler_received"
            shipment.job.submission.save(update_fields=["status"])

        return Response(IncomingShipmentSerializer(shipment).data)


class BatchListView(generics.ListAPIView):
    serializer_class   = ProcessingBatchSerializer
    permission_classes = [IsRecycler]

    def get_queryset(self):
        qs = ProcessingBatch.objects.filter(
            recycler__user=self.request.user
        ).select_related("material").order_by("-started_at")

        stage = self.request.query_params.get("stage")
        if stage:
            qs = qs.filter(stage=stage)
        return qs


class UpdateBatchView(APIView):
    permission_classes = [IsRecycler]

    def patch(self, request, pk):
        try:
            batch = ProcessingBatch.objects.get(
                pk=pk, recycler__user=request.user
            )
        except ProcessingBatch.DoesNotExist:
            return Response({"error": "Batch not found."}, status=404)

        new_stage     = request.data.get("stage", batch.stage)
        weight_out_kg = request.data.get("weight_out_kg")

        batch.stage = new_stage
        if weight_out_kg:
            batch.weight_out_kg = Decimal(str(weight_out_kg))

        if new_stage == "done":
            batch.completed_at = timezone.now()
            # Calculate revenue
            cash_rate = batch.material.cash_per_kg
            batch.revenue_generated = cash_rate * (batch.weight_out_kg or batch.weight_in_kg)
            # Update recycler totals
            recycler = batch.recycler
            recycler.total_kg_processed += batch.weight_in_kg
            recycler.total_revenue      += batch.revenue_generated
            recycler.save()
            # Deduct from inventory
            try:
                inv = MaterialInventory.objects.get(
                    recycler=recycler, material=batch.material
                )
                inv.quantity_kg = max(0, inv.quantity_kg - batch.weight_in_kg)
                inv.save()
            except MaterialInventory.DoesNotExist:
                pass

        batch.save()
        return Response(ProcessingBatchSerializer(batch).data)


class RevenueSummaryView(APIView):
    permission_classes = [IsRecycler]

    def get(self, request):
        recycler, _ = Recycler.objects.get_or_create(
            user=request.user,
            defaults={
                "company_name": f"{request.user.username} Recycler",
                "license_number": f"PENDING-{request.user.id}",
                "address": request.user.address or "Update your facility address",
            },
        )
        batches  = ProcessingBatch.objects.filter(recycler=recycler, stage="done")

        total_rev    = batches.aggregate(t=Sum("revenue_generated"))["t"] or 0
        total_paid   = batches.aggregate(t=Sum("user_credit_paid"))["t"] or 0
        margin       = round(((float(total_rev) - float(total_paid)) / max(float(total_rev), 1)) * 100, 1)

        data = {
            "total_revenue":          recycler.total_revenue,
            "this_month":             total_rev,
            "total_kg_processed":     recycler.total_kg_processed,
            "total_user_credits_paid": total_paid,
            "margin_pct":             margin,
        }
        serializer = RevenueSummarySerializer(data)
        return Response(serializer.data)
