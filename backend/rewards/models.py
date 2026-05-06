from django.db import models
from backend.users.models import User
from backend.waste.models import WasteSubmission

class Transaction(models.Model):
    TYPE_CHOICES = [
        ('points_earned', 'Points Earned'),
        ('cash_earned', 'Cash Earned'),
        ('tier_bonus', 'Tier Bonus'),
        ('referral_bonus', 'Referral Bonus'),
        ('cash_withdrawn', 'Cash Withdrawn'),
        ('penalty', 'Penalty'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    submission = models.ForeignKey(WasteSubmission, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_type = models.CharField(max_length=25, choices=TYPE_CHOICES)
    points = models.IntegerField(default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.transaction_type} — {self.points}pts"


class WithdrawalRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=100)
    paystack_reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — ₦{self.amount} — {self.status}"
