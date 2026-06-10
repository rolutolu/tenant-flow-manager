"""Admin page — user account management (admin-only)."""

from nicegui import ui
from app.auth import require_role, get_user_id, create_user, get_all_users, delete_user, reset_user_password
from app.services.audit_service import get_audit_logs
from app.theme import (page_layout, section_header, ACCENT, SUCCESS, DANGER,
                        TEXT_SECONDARY, CARD_BG, BORDER, TEXT_PRIMARY)


@ui.page("/admin")
@require_role("admin")
def admin_page():
    with page_layout(title="Admin Panel"):
        section_header("User Management", "Create and manage user accounts")

        with ui.row().classes("w-full gap-6 flex-wrap items-start"):

            # ── Create New User Card ──────────────────────────────────────
            with ui.card().classes("p-6 rounded-2xl shadow-sm card-hover flex-1 min-w-[380px]").style(
                f"background: {CARD_BG}; border: 1px solid {BORDER}"
            ):
                with ui.row().classes("items-center gap-3 mb-4"):
                    with ui.element("div").classes("rounded-xl p-2.5").style(
                        f"background: linear-gradient(135deg, {ACCENT}18, {ACCENT}08);"
                    ):
                        ui.icon("person_add", size="24px").style(f"color: {ACCENT}")
                    ui.label("Create New Account").classes("text-lg font-semibold")

                ui.label(
                    "Add team members with role-based permissions"
                ).classes("text-sm mb-4").style(f"color: {TEXT_SECONDARY}")

                new_username = ui.input(label="Username").classes("w-full").props("outlined")
                new_password = ui.input(
                    label="Password", password=True, password_toggle_button=True
                ).classes("w-full").props("outlined")
                new_role = ui.select(
                    label="Role",
                    options={"manager": "Manager", "viewer": "Viewer"},
                    value="viewer",
                ).classes("w-full").props("outlined")

                # Role descriptions
                with ui.card().classes("w-full p-4 rounded-xl mt-2").style(
                    "background: #F8FAFC; border: 1px solid #E2E8F0"
                ):
                    ui.label("Role Permissions").classes("text-xs font-bold tracking-wider mb-2").style(
                        f"color: {TEXT_SECONDARY}"
                    )
                    with ui.column().classes("gap-1.5"):
                        with ui.row().classes("items-center gap-2"):
                            ui.badge("Manager", color="#6366F1").classes("text-xs")
                            ui.label("Can view, add & edit tenants and leases").classes(
                                "text-xs"
                            ).style(f"color: {TEXT_SECONDARY}")
                        with ui.row().classes("items-center gap-2"):
                            ui.badge("Viewer", color="#94A3B8").classes("text-xs")
                            ui.label("Read-only access to dashboard & actions").classes(
                                "text-xs"
                            ).style(f"color: {TEXT_SECONDARY}")

                create_result = ui.label("").classes("text-sm mt-2")
                create_result.set_visibility(False)

                def handle_create():
                    if not new_username.value or not new_password.value:
                        ui.notify("Username and password are required", type="warning")
                        return
                    admin_id = get_user_id()
                    success, msg = create_user(
                        new_username.value, new_password.value,
                        new_role.value, created_by=admin_id,
                    )
                    if success:
                        create_result.style(f"color: {SUCCESS}")
                        ui.notify(msg, type="positive")
                        new_username.value = ""
                        new_password.value = ""
                        refresh_users()
                    else:
                        create_result.style(f"color: {DANGER}")
                        ui.notify(msg, type="negative")
                    create_result.text = msg
                    create_result.set_visibility(True)

                ui.button("Create Account", on_click=handle_create, icon="add").classes(
                    "w-full mt-3"
                ).props("unelevated rounded").style(
                    f"background: linear-gradient(135deg, {ACCENT}, #8B5CF6) !important;"
                )

            # ── Existing Users Card ───────────────────────────────────────
            with ui.card().classes("p-6 rounded-2xl shadow-sm flex-1 min-w-[380px]").style(
                f"background: {CARD_BG}; border: 1px solid {BORDER}"
            ):
                with ui.row().classes("items-center gap-3 mb-4"):
                    with ui.element("div").classes("rounded-xl p-2.5").style(
                        f"background: linear-gradient(135deg, {ACCENT}18, {ACCENT}08);"
                    ):
                        ui.icon("group", size="24px").style(f"color: {ACCENT}")
                    ui.label("Active Users").classes("text-lg font-semibold")

                users_container = ui.column().classes("w-full gap-3")

                def refresh_users():
                    users_container.clear()
                    users = get_all_users()
                    current_user_id = get_user_id()
                    with users_container:
                        if not users:
                            ui.label("No users found.").classes("text-sm").style(
                                f"color: {TEXT_SECONDARY}"
                            )
                            return
                        for user in users:
                            role_colors = {
                                "admin": "#EF4444",
                                "manager": "#6366F1",
                                "viewer": "#94A3B8",
                            }
                            with ui.card().classes("w-full p-4 rounded-xl").style(
                                f"border: 1px solid {BORDER}"
                            ):
                                with ui.row().classes("items-center justify-between w-full"):
                                    with ui.row().classes("items-center gap-3"):
                                        with ui.element("div").classes("rounded-full p-2").style(
                                            f"background: {role_colors.get(user['role'], '#94A3B8')}15;"
                                        ):
                                            ui.icon("person", size="18px").style(
                                                f"color: {role_colors.get(user['role'], '#94A3B8')}"
                                            )
                                        with ui.column().classes("gap-0"):
                                            ui.label(user["username"]).classes(
                                                "text-sm font-semibold"
                                            ).style(f"color: {TEXT_PRIMARY}")
                                            ui.label(
                                                f"Created {user.get('created_at', 'N/A')[:10]}"
                                            ).classes("text-xs").style(f"color: {TEXT_SECONDARY}")
                                    with ui.row().classes("items-center gap-2"):
                                        ui.badge(
                                            user["role"].capitalize(),
                                            color=role_colors.get(user["role"], "#94A3B8"),
                                        ).classes("text-xs")
                                        # Don't allow deleting yourself
                                        if user["id"] != current_user_id:
                                            ui.button(
                                                icon="lock_reset",
                                                on_click=lambda _, uid=user["id"], uname=user["username"]: confirm_reset(uid, uname),
                                            ).props("flat round color=primary size=sm").tooltip("Reset Password")
                                            ui.button(
                                                icon="delete",
                                                on_click=lambda _, uid=user["id"], uname=user["username"]: confirm_delete(uid, uname),
                                            ).props("flat round color=negative size=sm").tooltip("Delete")

                def confirm_reset(uid: str, uname: str):
                    with ui.dialog() as dialog, ui.card().classes("p-6 rounded-2xl w-96"):
                        ui.label(f"Reset password for '{uname}'").classes("text-lg font-semibold mb-2")
                        new_pw = ui.input(
                            label="New Password", password=True, password_toggle_button=True
                        ).classes("w-full mb-4").props("outlined")
                        with ui.row().classes("gap-2 justify-end w-full"):
                            ui.button("Cancel", on_click=dialog.close).props("flat")

                            def do_reset():
                                success, msg = reset_user_password(uid, new_pw.value)
                                ui.notify(msg, type="positive" if success else "negative")
                                dialog.close()

                            ui.button("Reset", on_click=do_reset, icon="lock_reset").props(
                                "unelevated color=primary"
                            )
                    dialog.open()

                def confirm_delete(uid: str, uname: str):
                    with ui.dialog() as dialog, ui.card().classes("p-6 rounded-2xl"):
                        ui.label(f"Delete user '{uname}'?").classes("text-lg font-semibold mb-2")
                        ui.label("This action cannot be undone. All their data will remain.").classes(
                            "text-sm mb-4"
                        ).style(f"color: {TEXT_SECONDARY}")
                        with ui.row().classes("gap-2 justify-end w-full"):
                            ui.button("Cancel", on_click=dialog.close).props("flat")
                            def do_delete():
                                success, msg = delete_user(uid)
                                ui.notify(msg, type="positive" if success else "negative")
                                dialog.close()
                                refresh_users()
                            ui.button("Delete", on_click=do_delete, icon="delete").props(
                                "unelevated color=negative"
                            )
                    dialog.open()

                refresh_users()

        section_header("Audit Trail", "Recent system actions logged for compliance")

        admin_user_id = get_user_id()
        logs = get_audit_logs(admin_user_id, limit=100)
        if logs:
            log_rows = [
                {
                    "timestamp": (log.get("timestamp") or "")[:19],
                    "action": log.get("action", ""),
                    "entity_type": log.get("entity_type", ""),
                    "entity_id": log.get("entity_id", ""),
                    "detail": str(log.get("new_value") or log.get("old_value") or "")[:80],
                }
                for log in logs
            ]
            ui.table(
                columns=[
                    {"name": "timestamp", "label": "Time", "field": "timestamp", "align": "left"},
                    {"name": "action", "label": "Action", "field": "action", "align": "left"},
                    {"name": "entity_type", "label": "Entity", "field": "entity_type", "align": "left"},
                    {"name": "entity_id", "label": "ID", "field": "entity_id", "align": "left"},
                    {"name": "detail", "label": "Details", "field": "detail", "align": "left"},
                ],
                rows=log_rows,
            ).classes("w-full").props("flat bordered dense")
        else:
            ui.label("No audit logs yet.").classes("text-sm").style(f"color: {TEXT_SECONDARY}")
