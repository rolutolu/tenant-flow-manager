"""Login page — username/password authentication with rate limiting protection."""

from nicegui import ui
from app.auth import attempt_login, is_authenticated
from app.theme import PRIMARY, ACCENT, TEXT_SECONDARY, GLOBAL_CSS
from app.services.rate_limit_service import get_client_ip, check_rate_limit, record_attempt, clear_attempts


@ui.page("/login")
def login_page():
    """Render the login screen with rate limit protection."""
    if is_authenticated():
        ui.navigate.to("/")
        return

    # Inject global styles
    ui.add_head_html(f"<style>{GLOBAL_CSS}</style>")

    ui.colors(primary=PRIMARY, secondary=ACCENT, accent=ACCENT)

    # Full-page background (Deep charcoal)
    with ui.element("div").classes("absolute inset-0").style(
        "background-color: #120E0C;"
        "min-height: 100vh; display: flex; align-items: center; justify-content: center;"
    ):
        with ui.column().classes("items-center gap-6").style(
            "max-width: 420px; width: 100%; padding: 0 20px;"
        ):
            # Logo area
            with ui.row().classes("items-center gap-3 mb-2"):
                ui.image("/static/virix_logo.png").style(
                    "width: 42px; height: 42px; border-radius: 8px; object-fit: cover;"
                )
                with ui.column().classes("gap-0"):
                    ui.html('<div style="font-family: \'Playfair Display\', serif; font-style: italic; font-weight: 600; font-size: 1.6rem; color: #FFFFFF; line-height: 1; margin-top: -2px;">Virix.</div>')
                    ui.label("PROPERTY SUITE").classes("text-[10px] font-bold tracking-widest uppercase").style("color: #827B77; line-height: 1; margin-top: 1px;")

            # Login card
            with ui.card().classes("w-full p-8 rounded-2xl shadow-xl").style(
                "border: 1px solid #E6E4DF;"
                "background-color: #FFFFFF;"
            ):
                ui.label("Welcome Back").classes("text-xl font-bold mb-1").style(
                    "color: #1C1915; font-family: 'Inter', sans-serif;"
                )
                ui.label("Sign in to your account").classes("text-sm mb-5").style(
                    "color: #827B77;"
                )

                username_input = ui.input(
                    label="Username",
                ).classes("w-full mb-3").props('outlined')

                password_input = ui.input(
                    label="Password",
                    password=True,
                    password_toggle_button=True,
                ).classes("w-full mb-1").props('outlined')

                def handle_forgot_password():
                    ui.notify("Password recovery is not fully implemented yet. Please contact your administrator.", type="warning")

                with ui.row().classes("w-full justify-end mb-4"):
                    ui.button("Forgot Password?", on_click=handle_forgot_password).props("flat dense").classes("text-sm normal-case").style("color: #120E0C;")

                error_label = ui.label("").classes("text-sm").style("color: #EF4444")
                error_label.set_visibility(False)

                def handle_login():
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

                    success, msg = attempt_login(username, password)
                    if success:
                        clear_attempts(ip_key)
                        clear_attempts(user_key)
                        ui.navigate.to("/")
                    else:
                        record_attempt(user_key)
                        error_label.text = msg
                        error_label.set_visibility(True)

                password_input.on("keydown.enter", handle_login)

                ui.button("Sign In", on_click=handle_login, icon="login").classes(
                    "w-full mt-3"
                ).props("rounded unelevated size=lg").style(
                    "background: #120E0C !important; font-family: 'Inter', sans-serif; font-weight: 500;"
                )

            with ui.row().classes("items-center gap-2 mt-3"):
                ui.icon("cloud_done", size="14px").style("color: #827B77")
                ui.label("Secured by Supabase").classes("text-xs").style(
                    "color: #827B77"
                )


