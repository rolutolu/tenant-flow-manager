"""Login page — single shared password gatekeeper."""

from nicegui import ui
from app.auth import attempt_login, is_authenticated
from app.theme import PRIMARY, ACCENT, TEXT_SECONDARY


@ui.page("/login")
def login_page():
    """Render the login screen."""
    if is_authenticated():
        ui.navigate.to("/")
        return

    ui.colors(primary=PRIMARY, secondary=ACCENT, accent=ACCENT)

    with ui.column().classes(
        "absolute-center items-center gap-6"
    ).style("max-width: 400px; width: 100%"):

        # Logo area
        with ui.column().classes("items-center gap-2 mb-4"):
            with ui.element("div").classes("rounded-2xl p-4 mb-2").style(
                f"background: linear-gradient(135deg, {PRIMARY}, {ACCENT})"
            ):
                ui.icon("apartment", size="40px").classes("text-white")
            ui.label("Tenant Flow Manager").classes(
                "text-2xl font-bold tracking-wide"
            ).style(f"color: {PRIMARY}")
            ui.label("Property Management System").classes("text-sm").style(
                f"color: {TEXT_SECONDARY}"
            )

        # Login card
        with ui.card().classes("w-full p-8 rounded-2xl shadow-lg").style(
            "border: 1px solid #E2E8F0"
        ):
            ui.label("Sign In").classes("text-lg font-semibold mb-4").style(
                f"color: {PRIMARY}"
            )

            password_input = ui.input(
                label="Password",
                password=True,
                password_toggle_button=True,
            ).classes("w-full mb-2").props('outlined')

            error_label = ui.label("").classes("text-sm").style("color: #EF4444")
            error_label.set_visibility(False)

            def handle_login():
                if attempt_login(password_input.value):
                    ui.navigate.to("/")
                else:
                    error_label.text = "Incorrect password. Please try again."
                    error_label.set_visibility(True)

            password_input.on("keydown.enter", handle_login)

            ui.button("Sign In", on_click=handle_login, icon="login").classes(
                "w-full mt-2"
            ).props("rounded unelevated")

        ui.label("Default password: admin123").classes("text-xs mt-2").style(
            f"color: {TEXT_SECONDARY}"
        )
