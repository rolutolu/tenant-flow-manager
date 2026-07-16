"""Login page — username/password authentication with rate limiting protection."""

from nicegui import ui, run
from app.auth import attempt_login, login, is_authenticated
from app.theme import PRIMARY, ACCENT, TEXT_SECONDARY, GLOBAL_CSS
from app.services.rate_limit_service import get_client_ip, check_rate_limit, record_attempt, clear_attempts


@ui.page("/login")
def login_page():
    """Render the login screen with rate limit protection."""
    if is_authenticated():
        ui.navigate.to("/")
        return

    # Inject global styles and custom overrides to force input text visibility
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
    ui.add_head_html("<title>Sign In — Virix</title>")

    ui.colors(primary=PRIMARY, secondary=ACCENT, accent=ACCENT)

    # Full-page background (matching register page background)
    with ui.column().classes("w-full min-h-screen items-center justify-center gap-0").style(
        "background-color: #F6F5F3;"
    ):
        # Card (matching register page card)
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

                ui.label("Welcome Back").classes("text-2xl font-bold mt-4").style(
                    "color: #1C1915; font-family: 'Inter', sans-serif;"
                )
                ui.label("Sign in to your account").classes("text-sm text-center mt-1").style(
                    "color: #827B77;"
                )

            # Form fields
            username_input = ui.input(
                label="Username",
                placeholder="Enter your username",
            ).classes("w-full").props("outlined stack-label")

            password_input = ui.input(
                label="Password",
                password=True,
                password_toggle_button=True,
                placeholder="Enter your password",
            ).classes("w-full mt-2").props("outlined stack-label")

            def handle_forgot_password():
                ui.notify("Password recovery is not fully implemented yet. Please contact your administrator.", type="warning")

            with ui.row().classes("w-full justify-end mb-4"):
                ui.button("Forgot Password?", on_click=handle_forgot_password).props("flat dense").classes("text-sm normal-case").style("color: #120E0C;")

            error_label = ui.label("").classes("text-sm").style("color: #EF4444")
            error_label.set_visibility(False)

            async def handle_login():
                error_label.set_visibility(False)
                username = username_input.value.strip()
                password = password_input.value

                if not username:
                    error_label.text = "Username is required."
                    error_label.set_visibility(True)
                    return

                ip = get_client_ip()
                ip_key = f"login_ip:{ip}"
                user_key = f"login_user:{username.lower()}"

                # 1. Check IP rate limit (15 attempts/5 mins)
                ip_ok, ip_retry = check_rate_limit(ip_key, 15, 300)
                if not ip_ok:
                    error_label.text = f"Too many login attempts. Please wait {ip_retry} seconds."
                    error_label.set_visibility(True)
                    return

                # 2. Check Username rate limit (5 failed attempts/15 mins)
                user_ok, user_retry = check_rate_limit(user_key, 5, 900)
                if not user_ok:
                    error_label.text = f"Account temporarily locked. Please wait {user_retry} seconds."
                    error_label.set_visibility(True)
                    return

                record_attempt(ip_key)

                success, result = await run.io_bound(attempt_login, username, password)
                if success:
                    clear_attempts(ip_key)
                    clear_attempts(user_key)
                    login(result["id"], result["username"], result["role"])
                    ui.navigate.to("/")
                else:
                    record_attempt(user_key)
                    error_label.text = result
                    error_label.set_visibility(True)

            password_input.on("keydown.enter", handle_login)

            ui.button("Sign In", on_click=handle_login, icon="login").classes(
                "w-full mt-5"
            ).props("unelevated rounded").style(
                "background: linear-gradient(135deg, #120E0C, #3A3A3A) !important; color: white !important; padding: 12px 0; font-family: 'Inter', sans-serif; font-weight: 500;"
            )

            # Footer link
            with ui.row().classes("items-center justify-center gap-1 mt-6 w-full"):
                ui.label("Need an account?").classes("text-sm").style(
                    "color: #827B77;"
                )
                ui.label("Create one →").classes("text-sm font-semibold cursor-pointer").style(
                    "color: #120E0C;"
                ).on("click", lambda: ui.navigate.to("/register"))

            with ui.row().classes("items-center justify-center gap-2 mt-4 w-full"):
                ui.icon("cloud_done", size="14px").style("color: #827B77")
                ui.label("Secured by Supabase").classes("text-xs").style(
                    "color: #827B77"
                )


