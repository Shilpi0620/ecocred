import requests
from django.conf import settings

PAYSTACK_BASE = "https://api.paystack.co"

def verify_account(account_number: str, bank_code: str) -> dict:
    """Verify bank account before withdrawal."""
    r = requests.get(
        f"{PAYSTACK_BASE}/bank/resolve",
        params={"account_number": account_number, "bank_code": bank_code},
        headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    )
    return r.json()

def initiate_transfer(amount_naira: float, account_number: str, bank_code: str, name: str, reason: str) -> dict:
    """
    Step 1: Create transfer recipient
    Step 2: Initiate transfer
    """
    # Create recipient
    rec = requests.post(
        f"{PAYSTACK_BASE}/transferrecipient",
        json={"type": "nuban", "name": name, "account_number": account_number, "bank_code": bank_code, "currency": "NGN"},
        headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    ).json()
    recipient_code = rec['data']['recipient_code']

    # Initiate transfer (amount in kobo)
    transfer = requests.post(
        f"{PAYSTACK_BASE}/transfer",
        json={"source": "balance", "amount": int(amount_naira * 100), "recipient": recipient_code, "reason": reason},
        headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    ).json()

    return transfer