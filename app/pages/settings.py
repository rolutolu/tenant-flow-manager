"""Account settings — per-landlord email sender and footer."""

from nicegui import ui, run
from app.auth import require_role, get_user_id
from app.theme import page_layout, section_header, ACCENT, SUCCESS, WARNING, TEXT_SECONDARY, CARD_BG, BORDER
from app.services.email_config_service import (
    get_email_config,
    save_email_config,
    update_verification_status,
)
from app.services.ses_service import is_ses_configured, request_ses_verification


@ui.page("/settings")
@require_role("admin", "manager")
async def settings_page():
    user_id = get_user_id()
    config = await run.io_bound(get_email_config, user_id)

    with page_layout(title="Settings"):
        section_header("Email Settings", "Send notices from your own address with a custom footer")

        # ── Roadmap / Upcoming Features Notice ─────────────────────────────
        with ui.card().classes("w-full p-4 mb-4 max-w-xl").style(
            "background: rgba(18, 14, 12, 0.03); border: 1px dashed var(--border); border-radius: 12px; box-shadow: none;"
        ):
            with ui.row().classes("items-center gap-3"):
                ui.icon("info", size="20px").style("color: var(--text-secondary);")
                with ui.column().classes("gap-0"):
                    ui.label("Coming Soon: Automated Email Sending & Bank Email Scanning").classes("font-semibold text-xs").style(
                        "color: var(--text-primary);"
                    )
                    ui.label(
                        "Full automated email broadcasting and direct integration to scan incoming bank deposit alert emails "
                        "are soon-to-be-implemented features currently in active development."
                    ).classes("text-[11px]").style("color: var(--text-secondary);")

        if not is_ses_configured():
            with ui.card().classes("w-full p-4 mb-4").style("background: #FFFBEB; border: 1px solid #FDE68A;"):
                ui.label(
                    "AWS SES is not configured yet. Add AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, "
                    "and AWS_REGION to your .env file. You can still save your sender address below."
                ).classes("text-sm text-amber-900")

        with ui.card().classes("w-full p-6 max-w-xl").style(f"background: {CARD_BG}; border: 1px solid {BORDER}"):
            ui.label("Your sender identity").classes("text-lg font-semibold mb-1")
            ui.label(
                "Enter the email address tenants will see. Amazon SES will email you a confirmation "
                "link the first time — click it before sending."
            ).classes("text-sm mb-4").style(f"color: {TEXT_SECONDARY}")

            from_email = ui.input(
                label="Send from email",
                value=config.get("from_email") or "",
                placeholder="you@yourproperties.com",
            ).classes("w-full mb-2").props("outlined")
            from_name = ui.input(
                label="Display name (optional)",
                value=config.get("from_name") or "",
                placeholder="Oakwood Property Management",
            ).classes("w-full mb-2").props("outlined")
            reply_to = ui.input(
                label="Reply-to email (optional)",
                value=config.get("reply_to") or "",
                placeholder="Same as send-from if left blank",
            ).classes("w-full mb-2").props("outlined")
            footer_text = ui.textarea(
                label="Email footer",
                value=config.get("footer_text") or "",
                placeholder="John Smith\nOakwood Properties\n(555) 123-4567\n123 Main St",
            ).classes("w-full mb-4").props("outlined autogrow")

            status_label = ui.label("").classes("text-sm mb-3")

            async def refresh_status():
                ok, msg = await run.io_bound(update_verification_status, user_id)
                color = SUCCESS if ok else WARNING
                status_label.text = msg
                status_label.style(f"color: {color}")

            if config.get("from_email"):
                await refresh_status()

            async def handle_save():
                success, msg = await run.io_bound(
                    save_email_config,
                    user_id,
                    from_email.value,
                    from_name.value,
                    reply_to.value,
                    footer_text.value,
                )
                if not success:
                    ui.notify(msg, type="negative")
                    return
                ui.notify(msg, type="positive")
                ok, vmsg = await run.io_bound(request_ses_verification, from_email.value)
                ui.notify(vmsg, type="positive" if ok else "warning")
                await refresh_status()

            with ui.row().classes("gap-2 flex-wrap"):
                ui.button("Save & Verify Email", on_click=handle_save, icon="save").props("unelevated color=primary")
                ui.button("Refresh Status", on_click=refresh_status, icon="refresh").props("outline")

        with ui.card().classes("w-full p-4 mt-4 max-w-xl").style("background: #F8FAFC; border: 1px solid #E2E8F0"):
            ui.label("How it works").classes("font-semibold text-sm mb-2")
            with ui.column().classes("gap-1 text-sm").style(f"color: {TEXT_SECONDARY}"):
                ui.label("1. Enter your email and footer, then click Save & Verify Email.")
                ui.label("2. Open the verification email from Amazon Web Services and click the link.")
                ui.label("3. Click Refresh Status — when verified, all your outbound emails use this address.")
                ui.label("4. Leases, rent notices, NSF alerts, and reference emails include your footer.")

        # ── Notification Preferences ───────────────────────────────────────────
        section_header("Notification Preferences", "Control which setup nudges appear on your dashboard")

        from nicegui import app as nicegui_app
        _BANNER_MUTE_KEY = "dashboard_banners_muted"

        with ui.card().classes("w-full p-6 max-w-xl").style(
            f"background: {CARD_BG}; border: 1px solid {BORDER}"
        ):
            ui.label("Dashboard setup banners").classes("font-semibold mb-1")
            ui.label(
                "When enabled, Virix shows banner notifications on your dashboard if tenant data "
                "or Meta marketing tokens are missing. Turn this off to hide them permanently."
            ).classes("text-sm mb-4").style(f"color: {TEXT_SECONDARY}")

            currently_muted = nicegui_app.storage.user.get(_BANNER_MUTE_KEY, False)

            mute_toggle = ui.switch(
                "Mute all setup banners",
                value=currently_muted,
            )

            status_msg = ui.label(
                "Banners are currently muted." if currently_muted else "Banners are currently shown."
            ).classes("text-sm mt-2").style(
                f"color: {WARNING if currently_muted else SUCCESS}"
            )

            def on_mute_toggle(e):
                nicegui_app.storage.user[_BANNER_MUTE_KEY] = e.value
                # Also clear individual dismissals so they show again if un-muted
                if not e.value:
                    nicegui_app.storage.user.pop("banner_import_dismissed", None)
                    nicegui_app.storage.user.pop("banner_meta_dismissed", None)
                status_msg.text = "Banners are currently muted." if e.value else "Banners are currently shown."
                status_msg.style(f"color: {WARNING if e.value else SUCCESS}")
                ui.notify(
                    "Setup banners muted." if e.value else "Setup banners re-enabled.",
                    type="info",
                )

            mute_toggle.on("update:model-value", on_mute_toggle)

