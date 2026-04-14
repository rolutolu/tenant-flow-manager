"""Notification service: Twilio SMS and email simulation."""

import os
from app.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER


def send_reference_check(tenant_name: str, ref_phone: str,
                         ref_name: str = "Reference") -> tuple[bool, str]:
    """Send an SMS inquiry to a tenant reference via Twilio.

    Falls back to simulation if Twilio credentials are not configured.
    """
    message_body = (
        f"Hello {ref_name}, you have been listed as a reference for {tenant_name}. "
        f"Please reply YES to confirm they were a tenant/employee in good standing, "
        f"or call us at 1-800-555-0199 for any concerns. Thank you!"
    )

    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
        try:
            from twilio.rest import Client
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=message_body,
                from_=TWILIO_PHONE_NUMBER,
                to=ref_phone
            )
            return True, f"SMS sent to {ref_phone} successfully."
        except Exception as e:
            return False, f"Twilio error: {str(e)}"
    else:
        # Simulated
        print(f"[SIMULATED SMS to {ref_phone}]: {message_body}")
        return True, f"[Simulated] SMS sent to {ref_phone}."


def send_nsf_notice(tenant_name: str, unit: str, amount: float,
                    penalty: float = 25.0) -> tuple[bool, str]:
    """Send a 48-hour e-transfer notice for returned payments.

    In production this would send an email/SMS. Currently simulated.
    """
    total = amount + penalty
    message = (
        f"Dear {tenant_name},\n\n"
        f"Your pre-authorized debit for Unit {unit} in the amount of ${amount:,.2f} "
        f"has been returned. An administrative fee of ${penalty:,.2f} has been applied.\n\n"
        f"Total amount due: ${total:,.2f}\n\n"
        f"Please submit an e-transfer within 48 hours to avoid further action.\n"
    )
    print(f"[SIMULATED NSF NOTICE to {tenant_name}]:\n{message}")
    return True, f"48-hour e-transfer notice sent to {tenant_name}. Total due: ${total:,.2f}"


def send_lease_email(tenant_name: str, email: str, filepath: str) -> tuple[bool, str]:
    """Simulate sending a lease copy via email."""
    print(f"[SIMULATED EMAIL to {email}]: Lease agreement attached from {filepath}")
    return True, f"[Simulated] Lease emailed to {tenant_name} at {email}."


def send_rent_increase_email(tenant_name: str, email: str,
                             filepath: str) -> tuple[bool, str]:
    """Simulate sending a rent increase notice via email."""
    print(f"[SIMULATED EMAIL to {email}]: Rent increase notice attached from {filepath}")
    return True, f"[Simulated] Rent increase notice emailed to {tenant_name} at {email}."
