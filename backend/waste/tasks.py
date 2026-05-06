from celery import shared_task
import requests, time
from django.conf import settings
from .models import WasteSubmission, VerificationLog, Material

@shared_task
def process_ml_verification(submission_id):
    sub = WasteSubmission.objects.get(id=submission_id)
    sub.status = 'ml_processing'
    sub.save()

    try:
        start = time.time()
        res = requests.post(
            f"{settings.ML_SERVICE_URL}/verify",
            json={"image_url": sub.image.url},
            timeout=30
        )
        elapsed = int((time.time() - start) * 1000)

        if res.status_code == 200:
            data = res.json()
            label, confidence = data['predicted_material'], data['confidence']

            VerificationLog.objects.create(
                submission=sub,
                model_version=data.get('model_version', 'v1'),
                raw_output=data,
                predicted_label=label,
                confidence_score=confidence,
                processing_time_ms=elapsed
            )

            material = Material.objects.filter(slug=label).first()
            threshold = settings.ML_AUTO_APPROVE_THRESHOLD

            if material and confidence >= threshold:
                sub.ml_predicted_material = material
                sub.ml_confidence = confidence
                sub.ml_verified = True
                sub.status = 'ml_verified'
                sub.save()
                calculate_and_award_rewards.delay(submission_id)
            else:
                sub.status = 'manual_review'
                sub.save()
                # Notify admin for manual review
                from backend.notifications.tasks import notify_admin_review
                notify_admin_review.delay(submission_id)
        else:
            sub.status = 'manual_review'
            sub.save()

    except Exception as e:
        sub.status = 'manual_review'
        sub.save()
        print(f"ML error for submission {submission_id}: {e}")


@shared_task
def calculate_and_award_rewards(submission_id, manual=False):
    """
    Calculates reward = base reward × tier bonus multiplier.
    Awards points and cash atomically. Updates user tier.
    Auto-assigns nearest available aggregator.
    """
    from django.db import transaction as dbt
    from backend.rewards.models import Transaction
    from backend.aggregators.tasks import auto_assign_aggregator
    from backend.notifications.tasks import send_push
    from decimal import Decimal

    sub = WasteSubmission.objects.get(id=submission_id)
    material = sub.ml_predicted_material if not manual else sub.material

    if not material:
        return

    with dbt.atomic():
        base_pts = int(material.points_per_kg * sub.weight_kg)
        base_cash = material.cash_per_kg * sub.weight_kg

        # Apply tier bonus
        user = sub.user
        tier_bonus_pct = Decimal('0')
        if user.current_tier:
            tier_bonus_pct = user.current_tier.cash_bonus_pct

        bonus_multiplier = 1 + (tier_bonus_pct / 100)
        final_cash = base_cash * bonus_multiplier
        final_pts = base_pts  # Points not affected by tier bonus (only cash)

        sub.base_points = base_pts
        sub.tier_bonus_pct = tier_bonus_pct
        sub.points_awarded = final_pts
        sub.cash_awarded = final_cash
        sub.status = 'approved'
        sub.save()

        # Update user wallet
        user.total_points += final_pts
        user.wallet_balance += final_cash
        user.total_kg_recycled += sub.weight_kg
        user.save()

        # Check and upgrade tier
        tier_upgraded = user.update_tier()

        # Log transactions
        Transaction.objects.create(
            user=user, submission=sub,
            transaction_type='points_earned',
            points=final_pts,
            amount=final_cash,
            description=f'Recycled {sub.weight_kg}kg of {material.name}'
        )
        if tier_bonus_pct > 0:
            bonus_amount = final_cash - base_cash
            Transaction.objects.create(
                user=user, submission=sub,
                transaction_type='tier_bonus',
                points=0, amount=bonus_amount,
                description=f'{tier_bonus_pct}% {user.current_tier.name} tier bonus'
            )

    # Push notifications
    msg = f"✅ {sub.weight_kg}kg of {material.name} verified! You earned {final_pts} pts & ₦{final_cash}."
    if tier_upgraded:
        msg += f" 🎉 You've reached {user.current_tier.name} tier!"
    send_push.delay(user.id, "Submission Approved!", msg)

    # Auto-assign nearest aggregator
    auto_assign_aggregator.delay(submission_id)
