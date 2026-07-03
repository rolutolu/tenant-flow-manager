"""Notification service: Twilio SMS and Amazon SES email."""

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    SES_FROM_EMAIL,
)
from app.services.email_config_service import resolve_sender, append_footer
from app.services.ses_service import is_ses_configured, get_ses_client, check_ses_verification


def format_delivery_message(message: str, *, simulated: bool) -> str:
    """Prefix messages consistently so the UI can show delivery mode."""
    if simulated and not message.startswith("[Simulated]"):
        return f"[Simulated] {message}"
    return message


def _download_storage_attachment(filepath: str) -> tuple[str, bytes] | None:
    """Download a document from Supabase Storage for email attachment."""
    if not filepath:
        return None
    try:
        from app.models.database import get_client

        content = get_client().storage.from_("documents").download(filepath)
        filename = filepath.split("/")[-1]
        return filename, content
    except Exception as e:
        print(f"[ERROR] Could not download attachment {filepath}: {e}")
        return None


def send_email(
    to: str,
    subject: str,
    body_text: str,
    user_id: str = None,
    attachment_path: str = None,
) -> tuple[bool, str]:
    """Send an email via Amazon SES using per-account sender settings."""
    if not to:
        return False, "Recipient email is required."

    sender = resolve_sender(user_id) if user_id else {
        "source": SES_FROM_EMAIL,
        "from_email": SES_FROM_EMAIL,
        "reply_to": "",
        "footer_text": "",
    }
    body_text = append_footer(body_text, sender.get("footer_text", ""))
    source = sender.get("source") or SES_FROM_EMAIL

    attachment = None
    if attachment_path:
        attachment = _download_storage_attachment(attachment_path)

    if not is_ses_configured() or not source:
        print(f"[SIMULATED EMAIL to {to}] From: {source}\nSubject: {subject}\n{body_text}")
        if attachment:
            print(f"Attachment: {attachment[0]} ({len(attachment[1])} bytes)")
        return True, format_delivery_message(f"Email sent to {to}.", simulated=True)

    from_email = sender.get("from_email", source)
    verified, status = check_ses_verification(from_email)
    if not verified:
        return False, (
            f"Sender {from_email} is not verified in SES (status: {status}). "
            f"Go to Settings, save your email, and click the AWS verification link."
        )

    try:
        client = get_ses_client()

        if attachment:
            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = source
            msg["To"] = to
            if sender.get("reply_to"):
                msg["Reply-To"] = sender["reply_to"]
            msg.attach(MIMEText(body_text, "plain", "utf-8"))
            part = MIMEApplication(attachment[1])
            part.add_header("Content-Disposition", "attachment", filename=attachment[0])
            msg.attach(part)
            client.send_raw_email(
                Source=source,
                Destinations=[to],
                RawMessage={"Data": msg.as_string()},
            )
        else:
            message = {
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Text": {"Data": body_text, "Charset": "UTF-8"}},
            }
            kwargs = {
                "Source": source,
                "Destination": {"ToAddresses": [to]},
                "Message": message,
            }
            if sender.get("reply_to"):
                kwargs["ReplyToAddresses"] = [sender["reply_to"]]
            client.send_email(**kwargs)
        return True, f"Email sent to {to} from {from_email}."
    except Exception as e:
        return False, f"SES error: {str(e)}"


def send_sms(to_phone: str, body: str) -> tuple[bool, str]:
    """Send an SMS via Twilio. Falls back to a simulated log if credentials are missing."""
    if not to_phone:
        return False, "Recipient phone number is required."

    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER \
            and TWILIO_ACCOUNT_SID != "your_account_sid_here":
        try:
            from twilio.rest import Client

            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=body,
                from_=TWILIO_PHONE_NUMBER,
                to=to_phone,
            )
            return True, f"SMS sent to {to_phone} successfully."
        except Exception as e:
            return False, f"Twilio error: {str(e)}"

    print(f"[SIMULATED SMS to {to_phone}]: {body}")
    return True, format_delivery_message(f"SMS sent to {to_phone}.", simulated=True)



def send_reference_check(
    tenant_name: str, ref_phone: str, ref_name: str = "Reference"
) -> tuple[bool, str]:
    """Send an SMS inquiry to a tenant reference via Twilio."""
    message_body = (
        f"Hello {ref_name}, you have been listed as a reference for {tenant_name}. "
        f"Please reply YES to confirm they were a tenant/employee in good standing, "
        f"or call us at 1-800-555-0199 for any concerns. Thank you!"
    )
    return send_sms(ref_phone, message_body)


def send_reference_email(
    tenant_name: str,
    ref_email: str,
    ref_name: str = "Reference",
    user_id: str = None,
) -> tuple[bool, str]:
    """Send a reference check inquiry via email."""
    body = (
        f"Hello {ref_name},\n\n"
        f"You have been listed as a reference for {tenant_name}. "
        f"Please reply to this email to confirm they were a tenant/employee in good standing.\n\n"
        f"Thank you!"
    )
    return send_email(ref_email, f"Reference Check for {tenant_name}", body, user_id=user_id)


def send_nsf_notice(
    tenant_name: str,
    unit: str,
    amount: float,
    penalty: float = 25.0,
    email: str = "",
    user_id: str = None,
) -> tuple[bool, str]:
    """Send a 48-hour e-transfer notice for returned payments."""
    total = amount + penalty
    body = (
        f"Dear {tenant_name},\n\n"
        f"Your pre-authorized debit for Unit {unit} in the amount of ${amount:,.2f} "
        f"has been returned. An administrative fee of ${penalty:,.2f} has been applied.\n\n"
        f"Total amount due: ${total:,.2f}\n\n"
        f"Please submit an e-transfer within 48 hours to avoid further action.\n"
    )
    if email:
        success, msg = send_email(email, f"NSF Notice — Unit {unit}", body, user_id=user_id)
        if success:
            return True, f"NSF notice sent to {tenant_name}. Total due: ${total:,.2f}."
        return False, msg
    print(f"[SIMULATED NSF NOTICE to {tenant_name}]:\n{body}")
    return True, format_delivery_message(
        f"NSF notice logged for {tenant_name} (no email on file). Total due: ${total:,.2f}.",
        simulated=True,
    )


def send_lease_email(
    tenant_name: str, email: str, filepath: str, user_id: str = None
) -> tuple[bool, str]:
    """Send a lease copy via email with PDF attachment."""
    body = (
        f"Dear {tenant_name},\n\n"
        f"Please find your lease agreement attached. Review, sign, and return at your earliest convenience.\n\n"
        f"Thank you."
    )
    return send_email(
        email,
        f"Lease Agreement — {tenant_name}",
        body,
        user_id=user_id,
        attachment_path=filepath,
    )


def send_rent_increase_email(
    tenant_name: str, email: str, filepath: str, user_id: str = None
) -> tuple[bool, str]:
    """Send a rent increase notice via email with PDF attachment."""
    body = (
        f"Dear {tenant_name},\n\n"
        f"Please find attached your notice of rent increase. Sign and return a copy for our records.\n\n"
        f"Thank you."
    )
    return send_email(
        email,
        f"Notice of Rent Increase — {tenant_name}",
        body,
        user_id=user_id,
        attachment_path=filepath,
    )
