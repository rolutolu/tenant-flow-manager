"""MFA Challenge page — verifies the admin's one-time passcode sent via Twilio SMS."""

import time
from nicegui import ui, app
from app.theme import GLOBAL_CSS, PRIMARY, ACCENT, SURFACE


@ui.page("/mfa")
def mfa_page():
    """MFA verification page. Admins land here after password login."""
    ui.add_head_html(f"<style>{GLOBAL_CSS}</style>")
    ui.colors(primary=PRIMARY, secondary=ACCENT, accent=ACCENT)

    user_id = app.storage.user.get("user_id")
    role = app.storage.user.get("role")

    # If not partially logged in, send to login
    if not user_id or role != "admin":
        ui.navigate.to("/login")
        return

    # If already verified, go to dashboard
    if app.storage.user.get("mfa_verified", False):
        ui.navigate.to("/")
        return

    username = app.storage.user.get("username", "Admin")
    has_phone = bool(app.storage.user.get("mfa_phone", ""))

    with ui.column().classes("w-full items-center justify-center fade-in").style(
        f"min-height: 100vh; background-color: {SURFACE};"
    ):
        with ui.card().classes("p-10 w-full max-w-md").style(
            "border-radius: 20px; border: 1px solid #E6E4DF; "
            "box-shadow: 0 20px 60px rgba(26,22,21,0.08);"
        ):
            # Header
            with ui.column().classes("items-center gap-2 mb-8"):
                with ui.element("div").style(
                    "background-color: #120E0C; border-radius: 12px; "
                    "width: 48px; height: 48px; display: flex; "
                    "align-items: center; justify-content: center;"
                ):
                    ui.html(
                        '<span style="font-family: \'Playfair Display\', serif; '
                        'font-style: italic; font-weight: 700; font-size: 1.6rem; '
                        'color: #F9F6F0; line-height: 1;">V.</span>'
                    )
                ui.html(
                    '<div style="font-family: \'Playfair Display\', serif; '
                    'font-style: italic; font-weight: 600; font-size: 1.6rem; '
                    'color: #1C1915; margin-top: 4px;">Two-Factor Authentication</div>'
                )
                ui.label(
                    f"A verification code was sent to your phone."
                    if has_phone
                    else "Check the server terminal for your verification code."
                ).style(
                    "color: #827B77; font-size: 0.85rem; text-align: center; "
                    "font-family: 'Inter', sans-serif;"
                )

            # OTP input
            code_input = ui.input(
                placeholder="000000",
                label="6-Digit Code",
            ).classes("w-full text-center").props("maxlength=6 outlined")
            code_input.style("font-size: 1.5rem; letter-spacing: 0.5em; text-align: center;")

            error_label = ui.label("").style("color: #EF4444; font-size: 0.8rem; font-family: 'Inter', sans-serif; min-height: 1.2em;")

            def verify():
                entered = (code_input.value or "").strip()
                stored_otp = app.storage.user.get("mfa_otp", "")
                otp_expiry = app.storage.user.get("mfa_otp_expiry", 0)

                if not entered:
                    error_label.set_text("Please enter the 6-digit code.")
                    return

                if time.time() > otp_expiry:
                    error_label.set_text("This code has expired. Please log in again.")
                    return

                if entered == stored_otp:
                    # Clear the OTP from session and mark MFA complete
                    app.storage.user["mfa_verified"] = True
                    app.storage.user.pop("mfa_otp", None)
                    app.storage.user.pop("mfa_otp_expiry", None)
                    app.storage.user["last_activity"] = time.time()
                    ui.navigate.to("/")
                else:
                    error_label.set_text("Invalid code. Please try again.")
                    code_input.set_value("")

            code_input.on("keydown.enter", verify)

            ui.button("Verify", on_click=verify).classes("w-full mt-2").style(
                "background-color: #120E0C; color: white; font-family: 'Inter', sans-serif; "
                "font-weight: 600; font-size: 0.9rem; letter-spacing: 0.05em; "
                "border-radius: 10px; height: 46px;"
            )

            # Resend / Back to login
            with ui.row().classes("w-full justify-center mt-4 gap-4"):
                ui.link("← Back to Login", "/login").style(
                    "color: #827B77; font-size: 0.8rem; font-family: 'Inter', sans-serif; "
                    "text-decoration: none;"
                )
