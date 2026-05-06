from celery import shared_task
import math

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two coordinates."""
    R = 6371
    dlat = math.radians(float(lat2) - float(lat1))
    dlon = math.radians(float(lon2) - float(lon1))
    a = math.sin(dlat/2)**2 + math.cos(math.radians(float(lat1))) * math.cos(math.radians(float(lat2))) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

@shared_task
def auto_assign_aggregator(submission_id):
    from .models import Aggregator, PickupJob
    from backend.waste.models import WasteSubmission

    sub = WasteSubmission.objects.get(id=submission_id)
    if not sub.user.latitude or not sub.user.longitude:
        return

    # Find available, verified aggregators that accept this material
    candidates = Aggregator.objects.filter(
        is_verified=True,
        is_available=True,
        accepted_materials=sub.material
    )

    nearest = None
    min_dist = float('inf')

    for agg in candidates:
        if not agg.latitude or not agg.longitude:
            continue
        dist = haversine(sub.user.latitude, sub.user.longitude, agg.latitude, agg.longitude)
        if dist <= agg.service_radius_km and dist < min_dist:
            min_dist = dist
            nearest = agg

    if nearest:
        job = PickupJob.objects.create(
            submission=sub,
            aggregator=nearest,
            status='pending',
            distance_km=round(min_dist, 2)
        )
        sub.status = 'aggregator_assigned'
        sub.save()
        # Notify aggregator
        from backend.notifications.tasks import send_push
        send_push.delay(
            nearest.user.id,
            "New Pickup Request 📦",
            f"New {sub.material.name} pickup — {round(min_dist, 1)}km away. {sub.weight_kg}kg."
        )
