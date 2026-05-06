from django.db import models
from backend.users.models import User
from backend.waste.models import Material, WasteSubmission

class Aggregator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='aggregator_profile')
    company_name = models.CharField(max_length=200)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    service_radius_km = models.IntegerField(default=10)
    accepted_materials = models.ManyToManyField(Material, blank=True)
    commission_rate_pct = models.DecimalField(max_digits=5, decimal_places=2, default=8.0)
    is_verified = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_kg_collected = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_commission_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return self.company_name


class PickupJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_transit', 'In Transit'),
        ('collected', 'Collected'),
        ('forwarded', 'Forwarded to Recycler'),
        ('cancelled', 'Cancelled'),
    ]

    submission = models.OneToOneField(WasteSubmission, on_delete=models.CASCADE, related_name='pickup_job')
    aggregator = models.ForeignKey(Aggregator, on_delete=models.SET_NULL, null=True, related_name='jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    accepted_at = models.DateTimeField(null=True, blank=True)
    collected_at = models.DateTimeField(null=True, blank=True)
    forwarded_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Job #{self.id} — {self.aggregator} — {self.status}"


class AggregatorCommission(models.Model):
    aggregator = models.ForeignKey(Aggregator, on_delete=models.CASCADE, related_name='commissions')
    job = models.OneToOneField(PickupJob, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=[('pending','Pending'),('paid','Paid')], default='pending')
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


