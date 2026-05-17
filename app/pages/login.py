"""Login page — username/password authentication."""

from nicegui import ui
from app.auth import attempt_login, is_authenticated
from app.theme import PRIMARY, ACCENT, TEXT_SECONDARY, GLOBAL_CSS


@ui.page("/login")
def login_page():
    """Render the login screen."""
    if is_authenticated():
        ui.navigate.to("/")
        return

    # Inject global styles
    ui.add_head_html(f"<style>{GLOBAL_CSS}</style>")

    ui.colors(primary=PRIMARY, secondary=ACCENT, accent=ACCENT)

    # Full-page background
    with ui.element("div").classes("absolute inset-0").style(
        f"background: linear-gradient(135deg, {PRIMARY} 0%, #1E293B 40%, #334155 100%);"
        "min-height: 100vh; display: flex; align-items: center; justify-content: center;"
    ):
        with ui.column().classes("items-center gap-6").style(
            "max-width: 420px; width: 100%; padding: 0 20px;"
        ):
            # Logo area
            with ui.column().classes("items-center gap-3 mb-2"):
                with ui.element("div").classes("rounded-2xl p-5 mb-1").style(
                    f"background: linear-gradient(135deg, {ACCENT}, #8B5CF6);"
                    "box-shadow: 0 8px 32px rgba(99, 102, 241, 0.35);"
                ):
                    ui.icon("apartment", size="44px").classes("text-white")
                ui.label("Virix").classes(
                    "text-3xl font-bold tracking-wider text-white uppercase"
                )
                ui.label("Property Management Suite").classes("text-sm").style(
                    "color: #94A3B8"
                )

            # Login card
            with ui.card().classes("w-full p-8 rounded-2xl shadow-2xl").style(
                "background: rgba(255, 255, 255, 0.95);"
                "backdrop-filter: blur(20px);"
                "border: 1px solid rgba(255,255,255,0.2);"
            ):
                ui.label("Welcome Back").classes("text-xl font-bold mb-1").style(
                    f"color: {PRIMARY}"
                )
                ui.label("Sign in to your account").classes("text-sm mb-5").style(
                    f"color: {TEXT_SECONDARY}"
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
                    ui.button("Forgot Password?", on_click=handle_forgot_password).props("flat dense").classes("text-sm normal-case").style(f"color: {ACCENT}")

                error_label = ui.label("").classes("text-sm").style("color: #EF4444")
                error_label.set_visibility(False)

                def handle_login():
                    success, msg = attempt_login(username_input.value, password_input.value)
                    if success:
                        ui.navigate.to("/")
                    else:
                        error_label.text = msg
                        error_label.set_visibility(True)

                password_input.on("keydown.enter", handle_login)

                ui.button("Sign In", on_click=handle_login, icon="login").classes(
                    "w-full mt-3"
                ).props("rounded unelevated size=lg").style(
                    f"background: linear-gradient(135deg, {ACCENT}, #8B5CF6) !important;"
                )

            with ui.row().classes("items-center gap-2 mt-3"):
                ui.icon("cloud_done", size="14px").style("color: #94A3B8")
                ui.label("Secured by Supabase").classes("text-xs").style(
                    "color: #94A3B8"
                )
