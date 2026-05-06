from celery import shared_task
import requests
from django.conf import settings

@shared_task
def send_push(user_id, title, body):
    from backend.users.models import User
    user = User.objects.get(id=user_id)
    if not user.fcm_token:
        return

    requests.post(
        "https://fcm.googleapis.com/fcm/send",
        json={
            "to": user.fcm_token,
            "notification": {"title": title, "body": body},
            "data": {"click_action": "FLUTTER_NOTIFICATION_CLICK"}
        },
        headers={
            "Authorization": f"key={settings.FCM_SERVER_KEY}",
            "Content-Type": "application/json"
        }
    )

@shared_task
def notify_admin_review(submission_id):
    """Alert admins when ML confidence is too low for auto-approval."""
    from backend.users.models import User
    admins = User.objects.filter(role='admin', fcm_token__isnull=False).exclude(fcm_token='')
    for admin in admins:
        send_push.delay(admin.id, "Manual Review Required 🔍", f"Submission #{submission_id} needs review — low ML confidence.")
