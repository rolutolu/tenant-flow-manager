"""Audit Log page — view all system activity across tenants, leases, and users."""

import json
from datetime import datetime, timezone
from nicegui import ui, app as nicegui_app

from app.auth import require_role, get_user_id
from app.theme import page_layout, section_header, ACCENT, BORDER
from app.services.audit_service import get_audit_logs


# ── Action colour mapping ─────────────────────────────────────────────────────

ACTION_COLORS = {
    "create":  {"bg": "#ECFDF5", "text": "#065F46", "dot": "#10B981"},
    "update":  {"bg": "#EFF6FF", "text": "#1E40AF", "dot": "#3B82F6"},
    "delete":  {"bg": "#FEF2F2", "text": "#991B1B", "dot": "#EF4444"},
    "login":   {"bg": "#F5F3FF", "text": "#4C1D95", "dot": "#8B5CF6"},
    "logout":  {"bg": "#FFF7ED", "text": "#92400E", "dot": "#F59E0B"},
    "send":    {"bg": "#ECFDF5", "text": "#065F46", "dot": "#10B981"},
    "import":  {"bg": "#EFF6FF", "text": "#1E40AF", "dot": "#3B82F6"},
    "payment": {"bg": "#ECFDF5", "text": "#065F46", "dot": "#10B981"},
}
DEFAULT_COLOR = {"bg": "#F9FAFB", "text": "#374151", "dot": "#9CA3AF"}


def _action_badge(action: str):
    """Render a coloured pill badge for an action verb."""
    key = action.lower().split()[0]
    colors = ACTION_COLORS.get(key, DEFAULT_COLOR)
    ui.html(
        f'<span style="'
        f'background-color:{colors["bg"]}; color:{colors["text"]}; '
        f'font-family:Inter,sans-serif; font-size:0.7rem; font-weight:600; '
        f'padding:3px 10px; border-radius:99px; white-space:nowrap; '
        f'text-transform:uppercase; letter-spacing:0.05em;">'
        f'<span style="display:inline-block;width:6px;height:6px;border-radius:50%;'
        f'background:{colors["dot"]};margin-right:5px;vertical-align:middle;"></span>'
        f'{action}'
        f'</span>'
    )


def _fmt_timestamp(ts: str) -> str:
    """Convert ISO timestamp to a readable local-style string."""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y  %H:%M")
    except Exception:
        return ts or "—"


def _fmt_json(value) -> str:
    """Pretty-print a JSONB value for display."""
    if value is None:
        return "—"
    if isinstance(value, dict):
        return json.dumps(value, indent=2, default=str)
    return str(value)


@ui.page("/audit")
@require_role("admin")
def audit_log_page():
    """Admin-only audit log viewer."""

    with page_layout("Audit Log"):

        section_header("Audit Log", "Full activity trail across all users and entities")

        # ── Toolbar ───────────────────────────────────────────────────────────
        logs_container = ui.column().classes("w-full gap-0")
        filter_state = {"entity": "", "search": ""}

        ENTITY_TYPES = [
            "All", "tenant", "lease", "payment", "maintenance",
            "property", "unit", "user", "import", "marketing",
        ]

        def reload(entity_filter="", search_text=""):
            filter_state["entity"] = entity_filter
            filter_state["search"] = search_text
            _render_logs(logs_container, entity_filter, search_text)

        with ui.row().classes("w-full items-center gap-4 mb-2 flex-wrap"):
            # Entity type selector
            entity_select = ui.select(
                options=ENTITY_TYPES,
                value="All",
                label="Filter by Type",
            ).classes("min-w-[180px]").props("outlined dense")

            # Search input
            search_input = ui.input(
                placeholder="Search action or entity ID…",
            ).classes("flex-1 min-w-[200px]").props("outlined dense clearable")
            search_input.style("font-family: 'Inter', sans-serif;")

            ui.button(
                "Refresh",
                icon="refresh",
                on_click=lambda: reload(
                    "" if entity_select.value == "All" else entity_select.value,
                    search_input.value or "",
                ),
            ).props("flat dense").style(
                "color: #120E0C; font-family: 'Inter', sans-serif; font-weight: 600;"
            )

        entity_select.on(
            "update:model-value",
            lambda e: reload(
                "" if e.args == "All" else e.args,
                search_input.value or "",
            ),
        )
        search_input.on(
            "keydown.enter",
            lambda: reload(
                "" if entity_select.value == "All" else entity_select.value,
                search_input.value or "",
            ),
        )

        # ── Initial render ────────────────────────────────────────────────────
        _render_logs(logs_container, "", "")


def _render_logs(container: ui.column, entity_filter: str, search_text: str):
    """Fetch and render the log table inside *container*."""
    container.clear()

    with container:
        logs = get_audit_logs(limit=200, entity_type=entity_filter or None)

        # Client-side search filter
        if search_text:
            q = search_text.lower()
            logs = [
                r for r in logs
                if q in (r.get("action") or "").lower()
                or q in (r.get("entity_type") or "").lower()
                or q in (r.get("entity_id") or "").lower()
            ]

        if not logs:
            with ui.card().classes("w-full p-12 items-center").style(
                "border: 1px dashed #E6E4DF; border-radius: 16px; "
                "background: transparent; box-shadow: none;"
            ):
                ui.icon("history", size="48px").style("color: #D1CDC9;")
                ui.label("No audit log entries found").style(
                    "color: #9CA3AF; font-family: 'Inter', sans-serif; "
                    "font-size: 0.95rem; margin-top: 8px;"
                )
                ui.label(
                    "Actions like tenant updates, payment records, and logins "
                    "will appear here automatically."
                ).style(
                    "color: #C4BFBb; font-family: 'Inter', sans-serif; "
                    "font-size: 0.8rem; text-align: center; max-width: 360px;"
                )
            return

        # ── Table header ──────────────────────────────────────────────────────
        with ui.element("div").classes("w-full").style(
            "background: #FFFFFF; border: 1px solid #E6E4DF; "
            "border-radius: 16px; overflow: hidden;"
        ):
            # Column headers
            with ui.row().classes("w-full px-6 py-3 items-center").style(
                "border-bottom: 1px solid #F0EDE8; background: #FAFAF9;"
            ):
                ui.label("TIMESTAMP").style(
                    "font-family:'Inter',sans-serif; font-size:0.65rem; "
                    "font-weight:600; letter-spacing:0.12em; color:#9CA3AF; "
                    "width:160px; flex-shrink:0;"
                )
                ui.label("ACTION").style(
                    "font-family:'Inter',sans-serif; font-size:0.65rem; "
                    "font-weight:600; letter-spacing:0.12em; color:#9CA3AF; "
                    "width:180px; flex-shrink:0;"
                )
                ui.label("TYPE").style(
                    "font-family:'Inter',sans-serif; font-size:0.65rem; "
                    "font-weight:600; letter-spacing:0.12em; color:#9CA3AF; "
                    "width:120px; flex-shrink:0;"
                )
                ui.label("ENTITY ID").style(
                    "font-family:'Inter',sans-serif; font-size:0.65rem; "
                    "font-weight:600; letter-spacing:0.12em; color:#9CA3AF; "
                    "flex:1;"
                )
                ui.label("CHANGES").style(
                    "font-family:'Inter',sans-serif; font-size:0.65rem; "
                    "font-weight:600; letter-spacing:0.12em; color:#9CA3AF; "
                    "width:80px; text-align:right; flex-shrink:0;"
                )

            # ── Rows ──────────────────────────────────────────────────────────
            for i, log in enumerate(logs):
                row_bg = "#FFFFFF" if i % 2 == 0 else "#FDFCFB"
                has_changes = log.get("old_value") or log.get("new_value")

                with ui.expansion("").classes("w-full").style(
                    f"background:{row_bg}; border-bottom: 1px solid #F5F3F0;"
                ).props("dense hide-expand-icon" if not has_changes else "dense"):

                    # Expansion header slot = the row itself
                    with ui.row().classes("w-full px-6 py-3 items-center"):
                        # Timestamp
                        ui.label(_fmt_timestamp(log.get("timestamp", ""))).style(
                            "font-family:'Inter',sans-serif; font-size:0.82rem; "
                            "color:#6B7280; width:160px; flex-shrink:0;"
                        )
                        # Action badge
                        with ui.element("div").style("width:180px; flex-shrink:0;"):
                            _action_badge(log.get("action", "—"))
                        # Entity type pill
                        entity = (log.get("entity_type") or "").lower()
                        ui.label(entity.capitalize()).style(
                            "font-family:'Inter',sans-serif; font-size:0.82rem; "
                            "color:#374151; font-weight:500; width:120px; flex-shrink:0;"
                        )
                        # Entity ID (truncated)
                        eid = str(log.get("entity_id") or "—")
                        ui.label(eid[:24] + ("…" if len(eid) > 24 else "")).style(
                            "font-family:'Inter',sans-serif; font-size:0.8rem; "
                            "color:#9CA3AF; font-variant-numeric:tabular-nums; flex:1;"
                        )
                        # Changes indicator
                        if has_changes:
                            ui.icon("unfold_more", size="16px").style(
                                "color:#9CA3AF; width:80px; text-align:right;"
                            )
                        else:
                            ui.label("").style("width:80px;")

                    # Expanded diff panel (only rendered when has_changes)
                    if has_changes:
                        with ui.row().classes("w-full gap-4 px-6 pb-4"):
                            # Old value
                            with ui.column().classes("flex-1 gap-1"):
                                ui.label("BEFORE").style(
                                    "font-family:'Inter',sans-serif; font-size:0.6rem; "
                                    "font-weight:700; letter-spacing:0.12em; color:#9CA3AF;"
                                )
                                ui.code(_fmt_json(log.get("old_value"))).style(
                                    "font-size:0.75rem; border-radius:8px; "
                                    "background:#FEF2F2; color:#991B1B; "
                                    "padding:10px; white-space:pre-wrap; "
                                    "font-family:'JetBrains Mono',monospace; "
                                    "max-height:160px; overflow-y:auto;"
                                )
                            # New value
                            with ui.column().classes("flex-1 gap-1"):
                                ui.label("AFTER").style(
                                    "font-family:'Inter',sans-serif; font-size:0.6rem; "
                                    "font-weight:700; letter-spacing:0.12em; color:#9CA3AF;"
                                )
                                ui.code(_fmt_json(log.get("new_value"))).style(
                                    "font-size:0.75rem; border-radius:8px; "
                                    "background:#ECFDF5; color:#065F46; "
                                    "padding:10px; white-space:pre-wrap; "
                                    "font-family:'JetBrains Mono',monospace; "
                                    "max-height:160px; overflow-y:auto;"
                                )

        # Footer count
        ui.label(f"Showing {len(logs)} entries").style(
            "font-family:'Inter',sans-serif; font-size:0.75rem; "
            "color:#9CA3AF; margin-top:8px; text-align:right; width:100%;"
        )
