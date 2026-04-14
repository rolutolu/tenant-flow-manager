"""Marketing & Advertising Dashboard — placeholder for future API integrations."""

from nicegui import ui
from app.auth import require_auth
from app.theme import page_layout, section_header, ACCENT, TEXT_SECONDARY, WARNING


@ui.page("/marketing")
@require_auth
def marketing_page():
    with page_layout(title="Marketing"):
        section_header("Marketing & Advertising Dashboard",
                       "Track property listing performance across platforms")

        # ── Coming Soon Banner ─────────────────────────────────────────────
        with ui.card().classes("w-full p-6 rounded-xl shadow-sm").style(
            f"border: 1px solid #E2E8F0; background: linear-gradient(135deg, {ACCENT}08, {ACCENT}15)"
        ):
            with ui.row().classes("items-center gap-3"):
                ui.icon("construction", size="32px").style(f"color: {WARNING}")
                with ui.column().classes("gap-0"):
                    ui.label("Coming Soon").classes("text-lg font-bold")
                    ui.label(
                        "API integrations for marketplace advertising are under development. "
                        "The cards below show the planned features."
                    ).classes("text-sm").style(f"color: {TEXT_SECONDARY}")

        # ── Platform Cards ─────────────────────────────────────────────────
        with ui.row().classes("w-full gap-6 flex-wrap"):

            _platform_card(
                name="Realtor.ca",
                icon="home_work",
                description="Track property listing views, inquiries, and lead conversion rates.",
                metrics=[
                    ("Active Listings", "—"),
                    ("Total Views", "—"),
                    ("Inquiries", "—"),
                ],
            )

            _platform_card(
                name="Instagram",
                icon="photo_camera",
                description="Monitor post engagement, follower growth, and DM inquiries for rental listings.",
                metrics=[
                    ("Posts", "—"),
                    ("Engagement Rate", "—"),
                    ("DM Leads", "—"),
                ],
            )

            _platform_card(
                name="Facebook Marketplace",
                icon="storefront",
                description="Analyze listing performance, messages received, and response times.",
                metrics=[
                    ("Active Listings", "—"),
                    ("Messages", "—"),
                    ("Avg. Response", "—"),
                ],
            )

        # ── Placeholder Chart ──────────────────────────────────────────────
        with ui.card().classes("w-full p-6 rounded-xl shadow-sm").style(
            "border: 1px solid #E2E8F0"
        ):
            with ui.row().classes("items-center gap-2 mb-4"):
                ui.icon("trending_up", size="24px").style(f"color: {ACCENT}")
                ui.label("Lead Generation Overview").classes("text-lg font-semibold")

            ui.echart({
                "tooltip": {"trigger": "axis"},
                "legend": {"data": ["Realtor.ca", "Instagram", "Marketplace"]},
                "xAxis": {
                    "type": "category",
                    "data": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                },
                "yAxis": {"type": "value", "name": "Leads"},
                "series": [
                    {"name": "Realtor.ca", "type": "line", "smooth": True,
                     "data": [12, 15, 18, 14, 20, 22],
                     "itemStyle": {"color": "#3B82F6"}},
                    {"name": "Instagram", "type": "line", "smooth": True,
                     "data": [5, 8, 6, 10, 12, 9],
                     "itemStyle": {"color": "#E1306C"}},
                    {"name": "Marketplace", "type": "line", "smooth": True,
                     "data": [8, 10, 12, 9, 15, 18],
                     "itemStyle": {"color": "#1877F2"}},
                ],
            }).classes("w-full h-72")

            ui.label(
                "Note: This chart currently shows sample data. Connect your API "
                "keys in Settings to display real metrics."
            ).classes("text-xs mt-2").style(f"color: {TEXT_SECONDARY}")


def _platform_card(name: str, icon: str, description: str,
                   metrics: list[tuple[str, str]]):
    """A card representing a marketing platform integration."""
    with ui.card().classes("p-5 rounded-xl shadow-sm flex-1 min-w-[280px]").style(
        "border: 1px solid #E2E8F0"
    ):
        with ui.row().classes("items-center gap-3 mb-3"):
            with ui.element("div").classes("rounded-lg p-2").style(
                f"background: {ACCENT}15"
            ):
                ui.icon(icon, size="24px").style(f"color: {ACCENT}")
            ui.label(name).classes("text-lg font-semibold")
            ui.badge("Planned", color="orange").classes("ml-auto")

        ui.label(description).classes("text-sm mb-4").style(f"color: {TEXT_SECONDARY}")

        with ui.row().classes("w-full gap-4 flex-wrap"):
            for label, value in metrics:
                with ui.column().classes("gap-0 items-center"):
                    ui.label(value).classes("text-xl font-bold").style(f"color: {TEXT_SECONDARY}")
                    ui.label(label).classes("text-xs").style(f"color: {TEXT_SECONDARY}")
