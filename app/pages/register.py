"""Invite-code gated registration page.

A prospective client visits /register?code=<INVITE_CODE>, fills in
their desired admin credentials, and their first admin account is created.

The invite code is set via the INVITE_CODE environment variable.
If INVITE_CODE is empty/unset, the registration page is disabled entirely.
"""

from nicegui import ui, run, app as nicegui_app
from app.auth import create_user
from app.config import INVITE_CODE
from app.theme import GLOBAL_CSS, PRIMARY, ACCENT, SUCCESS, DANGER, TEXT_SECONDARY
from app.services.rate_limit_service import get_client_ip, check_rate_limit, record_attempt


@ui.page("/register")
def register_page():
    """Public invite-code registration page — creates the first admin for a new client."""
    ui.add_head_html(f"<style>{GLOBAL_CSS}</style>")
    ui.add_head_html("""
    <style>
    /* Force inputs on login/register to have dark text and labels, ignoring body.dark-mode */
    .q-field__native, .q-field__prefix, .q-field__suffix, .q-field__input {
        color: #1C1915 !important;
    }
    .q-field__label {
        color: #827B77 !important;
    }
    .q-field__bottom {
        color: #827B77 !important;
    }
    .q-field__native::placeholder, .q-field__input::placeholder {
        color: #A8A29E !important;
        opacity: 1 !important;
    }
    .q-field--outlined .q-field__control:before {
        border: 1px solid #D6D3D1 !important;
    }
    .q-field--outlined .q-field__control:hover:before {
        border: 1px solid #1C1915 !important;
    }
    .q-field--focused .q-field__control:after {
        border: 2px solid #120E0C !important;
    }
    </style>
    """)
    ui.add_head_html("<title>Create Account — Virix</title>")

    # ── Gate: invite code must be configured ──────────────────────────────────
    if not INVITE_CODE:
        with ui.column().classes("w-full h-screen items-center justify-center"):
            ui.icon("lock", size="48px").style(f"color: {TEXT_SECONDARY}")
            ui.label("Registration is currently closed.").classes("text-xl font-semibold mt-4")
            ui.label("Contact your Virix representative for access.").classes("text-sm mt-1").style(
                f"color: {TEXT_SECONDARY}"
            )
        return



    # Pull the code from query params on first load via JS
    ui.add_head_html("""
    <script>
    (function () {
        const params = new URLSearchParams(window.location.search);
        const code = params.get('code') || '';
        // Store in a hidden input so Python can read it on submit
        document.addEventListener('DOMContentLoaded', function () {
            const hidden = document.getElementById('invite-code-hidden');
            if (hidden) hidden.value = code;
        });
    })();
    </script>
    """)

    # ── Page shell ────────────────────────────────────────────────────────────
    with ui.column().classes("w-full min-h-screen items-center justify-center gap-0").style(
        "background-color: #F6F5F3;"
    ):
        # Card
        with ui.card().classes("p-10 rounded-3xl shadow-xl w-full max-w-md").style(
            "background: #FFFFFF; border: 1px solid #E6E4DF;"
        ):

            # Header
            with ui.column().classes("items-center gap-2 mb-8 w-full"):
                with ui.row().classes("items-center gap-3 cursor-pointer").on(
                    "click", lambda: ui.navigate.to("/login")
                ):
                    ui.image("/static/virix_logo.png").style(
                        "width: 40px; height: 40px; border-radius: 10px; object-fit: cover;"
                    )
                    ui.html(
                        '<div style="font-family: \'Playfair Display\', serif; font-style: italic; '
                        'font-weight: 600; font-size: 1.6rem; color: #120E0C; line-height: 1;">'
                        "Virix.</div>"
                    )

                ui.label("Create Your Account").classes("text-2xl font-bold mt-4").style(
                    "color: #1C1915;"
                )
                ui.label(
                    "Enter the invite code you received along with your desired login credentials."
                ).classes("text-sm text-center mt-1").style(f"color: {TEXT_SECONDARY}")

            # ── Form fields ───────────────────────────────────────────────────
            invite_input = ui.input(
                label="Invite Code",
                placeholder="Enter the code provided to you",
            ).classes("w-full").props("outlined stack-label")

            username_input = ui.input(
                label="Username",
                placeholder="Choose a username",
            ).classes("w-full mt-2").props("outlined stack-label")

            password_input = ui.input(
                label="Password",
                password=True,
                password_toggle_button=True,
                placeholder="Choose a strong password",
            ).classes("w-full mt-2").props("outlined stack-label")

            confirm_input = ui.input(
                label="Confirm Password",
                password=True,
                password_toggle_button=True,
                placeholder="Repeat your password",
            ).classes("w-full mt-2").props("outlined stack-label")

            result_label = ui.label("").classes("text-sm mt-2 text-center w-full")
            result_label.set_visibility(False)

            # ── Submit handler ────────────────────────────────────────────────
            async def handle_register():
                result_label.set_visibility(False)

                ip = get_client_ip()
                ip_key = f"register_ip:{ip}"

                # Check registration rate limit (3 attempts per 10 mins)
                ok, retry_after = check_rate_limit(ip_key, 3, 600)
                if not ok:
                    result_label.text = f"Too many registration attempts. Please wait {retry_after} seconds."
                    result_label.style(f"color: {DANGER}")
                    result_label.set_visibility(True)
                    ui.notify("Registration rate limit exceeded.", type="negative")
                    return

                record_attempt(ip_key)

                # Validate invite code
                if invite_input.value.strip() != INVITE_CODE:

                    result_label.text = "Invalid invite code. Please check with your Virix representative."
                    result_label.style(f"color: {DANGER}")
                    result_label.set_visibility(True)
                    ui.notify("Invalid invite code.", type="negative")
                    return

                if not username_input.value.strip():
                    ui.notify("Username is required.", type="warning")
                    return

                if len(password_input.value) < 8:
                    result_label.text = "Password must be at least 8 characters."
                    result_label.style(f"color: {DANGER}")
                    result_label.set_visibility(True)
                    ui.notify("Password too short.", type="warning")
                    return

                if password_input.value != confirm_input.value:
                    result_label.text = "Passwords do not match."
                    result_label.style(f"color: {DANGER}")
                    result_label.set_visibility(True)
                    ui.notify("Passwords do not match.", type="warning")
                    return

                success, msg = await run.io_bound(
                    create_user,
                    username=username_input.value.strip(),
                    password=password_input.value,
                    role="admin",
                    created_by=None,
                )

                if success:
                    result_label.text = "Account created! Redirecting to login…"
                    result_label.style(f"color: {SUCCESS}")
                    result_label.set_visibility(True)
                    ui.notify("Account created successfully!", type="positive")
                    ui.timer(1.8, lambda: ui.navigate.to("/login"), once=True)
                else:
                    result_label.text = msg
                    result_label.style(f"color: {DANGER}")
                    result_label.set_visibility(True)
                    ui.notify(msg, type="negative")

            ui.button("Create Account", on_click=handle_register, icon="person_add").classes(
                "w-full mt-5"
            ).props("unelevated rounded").style(
                f"background: linear-gradient(135deg, {PRIMARY}, #3A3A3A) !important; color: white !important; padding: 12px 0;"
            )

            # ── Footer link ───────────────────────────────────────────────────
            with ui.row().classes("items-center justify-center gap-1 mt-6 w-full"):
                ui.label("Already have an account?").classes("text-sm").style(
                    f"color: {TEXT_SECONDARY}"
                )
                ui.label("Sign in →").classes("text-sm font-semibold cursor-pointer").style(
                    f"color: {PRIMARY}"
                ).on("click", lambda: ui.navigate.to("/login"))
