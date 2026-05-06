from celery import shared_task

@shared_task
def create_incoming_shipment(job_id, recycler_id):
    from .models import Recycler, IncomingShipment
    from backend.aggregators.models import PickupJob

    job = PickupJob.objects.get(id=job_id)
    recycler = Recycler.objects.get(id=recycler_id)

    shipment = IncomingShipment.objects.create(
        recycler=recycler,
        job=job,
        expected_weight_kg=job.submission.weight_kg,
        status='incoming'
    )
    # Notify recycler
    from backend.notifications.tasks import send_push
    send_push.delay(
        recycler.user.id,
        "Incoming Shipment 🚛",
        f"{job.submission.weight_kg}kg of {job.submission.material.name} on the way from {job.aggregator.company_name}."
    )
    return shipment.id
