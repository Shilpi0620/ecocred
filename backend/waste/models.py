from django.db import models
from backend.users.models import User

class Material(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=10)
    points_per_kg = models.DecimalField(max_digits=8, decimal_places=2)
    cash_per_kg = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class WasteSubmission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('ml_processing', 'ML Processing'),
        ('ml_verified', 'ML Verified'),
        ('manual_review', 'Manual Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('aggregator_assigned', 'Aggregator Assigned'),
        ('collected', 'Collected'),
        ('recycler_received', 'Recycler Received'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True)
    image = models.ImageField(upload_to='submissions/')
    weight_kg = models.DecimalField(max_digits=8, decimal_places=2)
    notes = models.TextField(blank=True)
    preferred_pickup_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')

    # ML
    ml_predicted_material = models.ForeignKey(
        Material, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ml_predictions'
    )
    ml_confidence = models.FloatField(null=True, blank=True)
    ml_verified = models.BooleanField(default=False)
    manually_reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_submissions'
    )

    # Rewards (computed on approval)
    base_points = models.PositiveIntegerField(default=0)
    tier_bonus_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    points_awarded = models.PositiveIntegerField(default=0)
    cash_awarded = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} — {self.material} — {self.weight_kg}kg"


class VerificationLog(models.Model):
    submission = models.ForeignKey(WasteSubmission, on_delete=models.CASCADE, related_name='logs')
    model_version = models.CharField(max_length=50)
    raw_output = models.JSONField()
    predicted_label = models.CharField(max_length=100)
    confidence_score = models.FloatField()
    processing_time_ms = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
