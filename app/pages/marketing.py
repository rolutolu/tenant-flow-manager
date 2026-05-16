"""Marketing Dashboard — Meta Marketing API integration (Facebook & Instagram)."""

from nicegui import ui
from app.auth import require_auth, get_user_id
from app.theme import page_layout, section_header, ACCENT, TEXT_SECONDARY, WARNING, CARD_BG, BORDER, SUCCESS
from app.services.marketing_service import is_meta_configured, get_ads, get_account_insights, save_marketing_config


@ui.page("/marketing")
@require_auth
def marketing_page():
    user_id = get_user_id()
    configured = is_meta_configured(user_id)

    with page_layout(title="Marketing"):
        # ── Configuration Alert & Form ────────────────────────────────────
        if not configured:
            with ui.card().classes("w-full p-6 mb-6 shadow-lg border-2 border-amber-200").style("background: #FFFBEB;"):
                with ui.column().classes("w-full gap-4"):
                    with ui.row().classes("items-center gap-3"):
                        ui.icon("settings", color="warning", size="32px")
                        ui.label("Meta API Setup Required").classes("text-xl font-bold text-amber-900")
                    
                    ui.label("Connect your Facebook Ad Account to track your property listings and performance metrics.").classes("text-amber-800")
                    
                    with ui.row().classes("w-full gap-4 flex-wrap"):
                        token_input = ui.input(label="Meta Access Token").classes("flex-1 min-w-[300px]").props("outlined password password-toggle-button")
                        acc_id_input = ui.input(label="Ad Account ID (act_...)").classes("flex-1 min-w-[200px]").props("outlined")
                    
                    async def handle_save_config():
                        if not token_input.value or not acc_id_input.value:
                            ui.notify("Both fields are required", type="warning")
                            return
                        if save_marketing_config(user_id, token_input.value, acc_id_input.value):
                            ui.notify("Meta configuration saved successfully!", type="positive")
                            ui.navigate.to("/marketing") # Refresh
                        else:
                            ui.notify("Failed to save configuration", type="negative")

                    ui.button("Save & Connect", on_click=handle_save_config, icon="bolt").props("unelevated color=warning rounded")
                    ui.label("Don't have these? Visit the Meta for Developers portal.").classes("text-xs text-amber-700")

        section_header("Marketing & Advertising", "Manage your Meta (Facebook & Instagram) property listings")

        # Container for content that will be blurred if not configured
        with ui.element("div").classes("w-full relative") as container:
            if not configured:
                container.classes("blur-content")
                # Transparent overlay to prevent clicks if someone tries to inspect-element remove the blur
                with ui.element("div").classes("lock-overlay"):
                    with ui.card().classes("p-8 items-center gap-4 text-center shadow-2xl"):
                        ui.icon("lock", size="64px", color="grey-4")
                        ui.label("Marketing Data Locked").classes("text-xl font-bold")
                        ui.label("Please configure your Meta Marketing API keys to unlock this dashboard.").classes("text-slate-500 max-w-xs")

            # ── Main Content Area ──────────────────────────────────────────
            with ui.column().classes("w-full gap-6"):

                # ── Listings Section ───────────────────────────────────────
                with ui.card().classes("w-full p-6 rounded-2xl shadow-sm").style(f"background: {CARD_BG}; border: 1px solid {BORDER}"):
                    with ui.row().classes("items-center justify-between w-full mb-4"):
                        with ui.row().classes("items-center gap-3"):
                            with ui.element("div").classes("rounded-xl p-2.5").style(f"background: {ACCENT}18;"):
                                ui.icon("campaign", size="24px").style(f"color: {ACCENT}")
                            ui.label("Current Property Listings").classes("text-lg font-semibold")
                        ui.button("Refresh Ads", on_click=lambda: refresh_listings()).props("outline icon=refresh")

                    listings_grid = ui.row().classes("w-full gap-4 flex-wrap")

                    def refresh_listings():
                        listings_grid.clear()
                        if not configured:
                            with listings_grid:
                                for _ in range(3): _placeholder_listing()
                            return

                        success, ads, err = get_ads(user_id)
                        with listings_grid:
                            if success and ads:
                                for ad in ads:
                                    _listing_card(ad)
                            else:
                                ui.notify(f"API Error: {err}", type="negative")
                                for _ in range(3): _placeholder_listing()

                    refresh_listings()

                # ── Analytics Section ──────────────────────────────────────
                with ui.row().classes("w-full gap-6 flex-wrap"):
                    # Facebook Stats
                    with ui.card().classes("flex-1 min-w-[300px] p-6 rounded-2xl shadow-sm").style(f"background: {CARD_BG}; border: 1px solid {BORDER}"):
                        with ui.row().classes("items-center gap-3 mb-4"):
                            ui.icon("facebook", color="blue-8", size="32px")
                            ui.label("Facebook Performance").classes("text-lg font-semibold")

                        insights = get_account_insights(user_id)[1] if configured else {}
                        _mini_stat("Reach", insights.get("reach", "0"), "groups")
                        _mini_stat("Spend", f"${insights.get('spend', '0.00')}", "payments")

                    # Instagram Stats
                    with ui.card().classes("flex-1 min-w-[300px] p-6 rounded-2xl shadow-sm").style(f"background: {CARD_BG}; border: 1px solid {BORDER}"):
                        with ui.row().classes("items-center gap-3 mb-4"):
                            ui.icon("camera_alt", color="pink-6", size="32px")
                            ui.label("Instagram Performance").classes("text-lg font-semibold")

                        _mini_stat("Impressions", insights.get("impressions", "0"), "visibility")
                        _mini_stat("CTR", f"{insights.get('ctr', '0.00')}%", "ads_click")


def _listing_card(ad: dict):
    """Render a single Meta Ad listing."""
    creative = ad.get("creative", {})
    image = creative.get("image_url") or creative.get("thumbnail_url") or "https://via.placeholder.com/300x200?text=No+Image"

    with ui.card().classes("w-72 overflow-hidden rounded-xl shadow-sm border border-slate-100"):
        ui.image(image).classes("w-full h-40 object-cover")
        with ui.column().classes("p-4 gap-1"):
            ui.label(ad.get("name", "Unnamed Ad")).classes("font-bold truncate w-full")
            status = ad.get("status", "UNKNOWN")
            color = SUCCESS if status == "ACTIVE" else WARNING
            ui.badge(status, color=color).classes("text-[10px] w-fit")
            ui.label(creative.get("body", "")).classes("text-xs text-slate-500 line-clamp-2 mt-1")


def _placeholder_listing():
    """Sample card shown when API is not connected."""
    with ui.card().classes("w-72 overflow-hidden rounded-xl opacity-40 border border-dashed border-slate-300"):
        ui.element("div").classes("w-full h-40 bg-slate-200")
        with ui.column().classes("p-4 gap-2"):
            ui.element("div").classes("w-3/4 h-4 bg-slate-200 rounded")
            ui.element("div").classes("w-1/2 h-3 bg-slate-100 rounded")


def _mini_stat(label: str, value: str, icon: str):
    """Small stat row for the performance cards."""
    with ui.row().classes("items-center justify-between w-full py-2 border-b border-slate-50 last:border-0"):
        with ui.row().classes("items-center gap-2"):
            ui.icon(icon, size="16px", color="grey-6")
            ui.label(label).classes("text-sm text-slate-600")
        ui.label(str(value)).classes("font-bold text-slate-800")
