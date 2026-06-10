"""Amazon SES client helpers."""

from app.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION


def is_ses_configured() -> bool:
    """Return True when Amazon SES API credentials are set."""
    return bool(AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY)


def get_ses_client():
    import boto3

    return boto3.client(
        "ses",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


def request_ses_verification(email: str) -> tuple[bool, str]:
    """Ask Amazon SES to send a verification link to the landlord's address."""
    if not is_ses_configured():
        return False, "AWS SES is not configured. Add AWS keys to .env first."
    if not email or "@" not in email:
        return False, "Invalid email address."

    try:
        get_ses_client().verify_email_identity(EmailAddress=email.strip())
        return True, f"Verification email sent to {email}. Click the link AWS sends you, then refresh status here."
    except Exception as e:
        return False, f"SES verification error: {str(e)}"


def check_ses_verification(email: str) -> tuple[bool, str]:
    """Check whether an address is verified in Amazon SES."""
    if not is_ses_configured() or not email:
        return False, "Not verified"

    try:
        resp = get_ses_client().get_identity_verification_attributes(Identities=[email.strip()])
        attrs = resp.get("VerificationAttributes", {}).get(email.strip(), {})
        status = attrs.get("VerificationStatus", "NotStarted")
        return status == "Success", status
    except Exception as e:
        print(f"SES verification check error: {e}")
        return False, "Unknown"
