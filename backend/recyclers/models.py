from django.db import models
from backend.users.models import User
from backend.waste.models import Material
from backend.aggregators.models import PickupJob

class Recycler(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recycler_profile')
    company_name = models.CharField(max_length=200)
    license_number = models.CharField(max_length=100, unique=True)
    address = models.TextField()
    accepted_materials = models.ManyToManyField(Material, blank=True)
    is_verified = models.BooleanField(default=False)
    total_kg_processed = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return self.company_name


class MaterialInventory(models.Model):
    """Real-time stock tracker per recycler per material."""
    recycler = models.ForeignKey(Recycler, on_delete=models.CASCADE, related_name='inventory')
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('recycler', 'material')

    def __str__(self):
        return f"{self.recycler} — {self.material} — {self.quantity_kg}kg"


class IncomingShipment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('incoming', 'Incoming'),
        ('received', 'Received'),
        ('rejected', 'Rejected'),
    ]
    recycler = models.ForeignKey(Recycler, on_delete=models.CASCADE, related_name='shipments')
    job = models.OneToOneField(PickupJob, on_delete=models.CASCADE, related_name='shipment')
    expected_weight_kg = models.DecimalField(max_digits=8, decimal_places=2)
    actual_weight_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    eta = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    received_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Shipment #{self.id} — {self.recycler}"


class ProcessingBatch(models.Model):
    STAGE_CHOICES = [
        ('received', 'Received'),
        ('qc', 'QC Check'),
        ('processing', 'Processing'),
        ('done', 'Completed'),
    ]
    recycler = models.ForeignKey(Recycler, on_delete=models.CASCADE, related_name='batches')
    shipment = models.ForeignKey(IncomingShipment, on_delete=models.SET_NULL, null=True, blank=True)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    weight_in_kg = models.DecimalField(max_digits=8, decimal_places=2)
    weight_out_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='received')
    revenue_generated = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    user_credit_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    @property
    def yield_pct(self):
        if self.weight_out_kg and self.weight_in_kg:
            return round((self.weight_out_kg / self.weight_in_kg) * 100, 1)
        return None

    def __str__(self):
        return f"Batch #{self.id} — {self.material} — {self.stage}"
