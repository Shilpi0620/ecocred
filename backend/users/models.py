from django.contrib.auth.models import AbstractUser
from django.db import models

class RewardTier(models.Model):
    """Bronze / Silver / Gold / Platinum tiers."""
    name = models.CharField(max_length=50)          # e.g. "Silver"
    min_points = models.PositiveIntegerField()       # 250
    max_points = models.PositiveIntegerField(null=True, blank=True)  # 499
    cash_bonus_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 5.00
    priority_collection = models.BooleanField(default=False)
    dedicated_aggregator = models.BooleanField(default=False)
    instant_payout = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['min_points']

    def __str__(self):
        return self.name


class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'User/Recycler'),
        ('aggregator', 'Aggregator'),
        ('recycler', 'Recycler'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    phone = models.CharField(max_length=20, blank=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Wallet
    wallet_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_points = models.PositiveIntegerField(default=0)
    total_kg_recycled = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Tier
    current_tier = models.ForeignKey(
        RewardTier, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='users'
    )

    # Push notifications
    fcm_token = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def update_tier(self):
        """Auto-upgrade tier based on current total_points."""
        tier = RewardTier.objects.filter(
            min_points__lte=self.total_points
        ).order_by('-min_points').first()
        if tier and tier != self.current_tier:
            self.current_tier = tier
            self.save(update_fields=['current_tier'])
            return True
        return False

    def __str__(self):
        return f"{self.username} ({self.role})"
