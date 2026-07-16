from nicegui import ui, run
from app.auth import require_role, get_user_id, get_user_role, create_user, get_all_users, delete_user, reset_user_password
from app.services.audit_service import get_audit_logs
from app.services.import_submission_service import (
    get_pending_submissions, approve_submission, reject_submission, get_download_url,
)
from app.theme import (page_layout, section_header, ACCENT, SUCCESS, DANGER, WARNING,
                        TEXT_SECONDARY, CARD_BG, BORDER, TEXT_PRIMARY)


@ui.page("/admin")
@require_role("admin")
async def admin_page():
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

                async def handle_create():
                    if not new_username.value or not new_password.value:
                        ui.notify("Username and password are required", type="warning")
                        return
                    admin_id = get_user_id()
                    success, msg = await run.io_bound(
                        create_user,
                        new_username.value, new_password.value,
                        new_role.value, created_by=admin_id,
                    )
                    if success:
                        create_result.style(f"color: {SUCCESS}")
                        ui.notify(msg, type="positive")
                        new_username.value = ""
                        new_password.value = ""
                        await refresh_users()
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

                async def refresh_users():
                    users_container.clear()
                    users = await run.io_bound(get_all_users)
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

                            async def do_reset():
                                success, msg = await run.io_bound(reset_user_password, uid, new_pw.value)
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
                            async def do_delete():
                                success, msg = await run.io_bound(delete_user, uid)
                                ui.notify(msg, type="positive" if success else "negative")
                                dialog.close()
                                await refresh_users()
                            ui.button("Delete", on_click=do_delete, icon="delete").props(
                                "unelevated color=negative"
                            )
                    dialog.open()

                await refresh_users()

        # ── Pending Imports (superadmin only) ─────────────────────────────────
        if get_user_role() == "superadmin":
            pending = await run.io_bound(get_pending_submissions)
            _render_pending_imports(get_user_id(), pending)

        section_header("Audit Trail", "Recent system actions logged for compliance")

        admin_user_id = get_user_id()
        logs = await run.io_bound(get_audit_logs, admin_user_id, limit=100)
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


# ── Pending Imports renderer (superadmin only) ─────────────────────────────────

import math as _math

_REVIEW_ROWS_PER_PAGE = 50

_REVIEW_COLS = [
    {"name": "n",             "label": "#",           "field": "n",             "align": "right"},
    {"name": "property",      "label": "Property",    "field": "property",      "align": "left"},
    {"name": "unit",          "label": "Unit",        "field": "unit",          "align": "left"},
    {"name": "tenant",        "label": "Tenant",      "field": "tenant",        "align": "left"},
    {"name": "rent",          "label": "Rent",        "field": "rent",          "align": "right"},
    {"name": "email",         "label": "Email",       "field": "email",         "align": "left"},
    {"name": "lease_start",   "label": "Lease Start", "field": "lease_start",   "align": "left"},
    {"name": "lease_end",     "label": "Lease End",   "field": "lease_end",     "align": "left"},
    {"name": "move_in_status","label": "Move-In",     "field": "move_in_status","align": "left"},
    {"name": "banking_set_up","label": "Banking",     "field": "banking_set_up","align": "left"},
    {"name": "lease_signed",  "label": "Signed",      "field": "lease_signed",  "align": "left"},
    {"name": "edit_btn",      "label": "",            "field": "edit_btn",      "align": "center"},
]


def _render_pending_imports(reviewer_id: str, pending: list):
    """Render the Pending Imports review section for the superadmin."""

    badge = f" ({len(pending)})" if pending else ""
    section_header(f"Pending Imports{badge}", "Review, edit, and approve client data submissions")

    if not pending:
        ui.label("No pending imports — all clear.").classes("text-sm").style(f"color: {TEXT_SECONDARY}")
        return

    # local_edits: sub_id → list[dict]  (mutable copy of mapped_rows for inline edits)
    local_pages: dict[str, int] = {}

    for sub in pending:
        sub_id    = sub["id"]
        submitter = (sub.get("submitter") or {}).get("username", "Unknown")
        fname     = sub.get("filename", "unknown")
        ftype     = sub.get("file_type", "raw")
        row_count = sub.get("row_count", 0)
        date      = (sub.get("submitted_at") or "")[:10]

        # Start with a fresh copy of the DB rows for this submission
        editable_rows: list[dict] = list(sub.get("mapped_rows") or [])
        local_pages[sub_id] = 1

        with ui.card().classes("w-full p-6 mb-4 shadow-sm").style(
            f"background: {CARD_BG}; border: 1px solid {BORDER}"
        ):
            # ── Header row ─────────────────────────────────────────────────
            with ui.row().classes("items-start justify-between w-full mb-4 flex-wrap gap-3"):
                with ui.column().classes("gap-1"):
                    with ui.row().classes("items-center gap-2"):
                        icon = "table_chart" if ftype == "spreadsheet" else "attach_file"
                        ui.icon(icon, size="20px").style(f"color: {ACCENT}")
                        ui.label(fname).classes("text-lg font-semibold").style(f"color: {TEXT_PRIMARY}")
                    ui.label(
                        f"From: {submitter}  ·  {date}  ·  "
                        f"{ftype.capitalize()}"
                        + (f"  ·  {row_count} rows" if ftype == "spreadsheet" else "")
                    ).classes("text-sm").style(f"color: {TEXT_SECONDARY}")

                # Download button (always shown)
                with ui.row().classes("gap-2 items-center"):
                    storage_path = sub.get("storage_path")
                    if storage_path:
                        def open_download(sp=storage_path):
                            url = get_download_url(sp)
                            if url:
                                ui.navigate.to(url, new_tab=True)
                            else:
                                ui.notify("Could not generate download link.", type="negative")

                        ui.button("Download File", on_click=open_download, icon="download").props(
                            "outline rounded size=sm"
                        )

            # ── Spreadsheet-only: paginated preview + row editing ───────────
            if ftype == "spreadsheet" and editable_rows:
                table_area = ui.column().classes("w-full")

                def render_review_table(sid=sub_id, rows=editable_rows, ta=table_area):
                    ta.clear()
                    total = len(rows)
                    page  = local_pages.get(sid, 1)
                    total_pages = max(1, _math.ceil(total / _REVIEW_ROWS_PER_PAGE))
                    page  = max(1, min(page, total_pages))
                    local_pages[sid] = page

                    start = (page - 1) * _REVIEW_ROWS_PER_PAGE
                    end   = min(start + _REVIEW_ROWS_PER_PAGE, total)

                    page_rows = [
                        {"n": start + i + 1, **r, "edit_btn": start + i}
                        for i, r in enumerate(rows[start:end])
                    ]

                    with ta:
                        tbl = ui.table(columns=_REVIEW_COLS, rows=page_rows).classes(
                            "w-full mb-2"
                        ).props("flat dense bordered")

                        tbl.add_slot("body-cell-edit_btn", """
                            <q-td :props="props">
                                <q-btn flat round dense size="sm" icon="edit" color="primary"
                                       @click="$parent.$emit('edit_row', props.row)" />
                            </q-td>
                        """)

                        def handle_edit_row(e, rows_ref=rows, sid=sid, rt=render_review_table):
                            row_data = e.args
                            idx = row_data.get("n", 1) - 1  # "n" is 1-indexed absolute position
                            if idx < 0 or idx >= len(rows_ref):
                                return
                            original = rows_ref[idx]

                            with ui.dialog() as dlg, ui.card().classes("p-6 w-[520px]"):
                                ui.label(f"Edit Row {idx + 1}").classes("text-lg font-semibold mb-4")
                                fields = {
                                    "property":       ui.input("Property",      value=str(original.get("property", ""))).classes("w-full mb-2").props("outlined dense"),
                                    "unit":           ui.input("Unit",          value=str(original.get("unit", ""))).classes("w-full mb-2").props("outlined dense"),
                                    "tenant":         ui.input("Tenant Name",   value=str(original.get("tenant", ""))).classes("w-full mb-2").props("outlined dense"),
                                    "rent":           ui.input("Rent",          value=str(original.get("rent", ""))).classes("w-full mb-2").props("outlined dense"),
                                    "email":          ui.input("Email",         value=str(original.get("email", ""))).classes("w-full mb-2").props("outlined dense"),
                                    "lease_start":    ui.input("Lease Start",   value=str(original.get("lease_start", ""))).classes("w-full mb-2").props("outlined dense"),
                                    "lease_end":      ui.input("Lease End",     value=str(original.get("lease_end", ""))).classes("w-full mb-2").props("outlined dense"),
                                    "move_in_status": ui.input("Move-In Status",value=str(original.get("move_in_status", ""))).classes("w-full mb-2").props("outlined dense"),
                                    "banking_set_up": ui.input("Banking Set Up",value=str(original.get("banking_set_up", ""))).classes("w-full mb-2").props("outlined dense"),
                                    "lease_signed":   ui.input("Lease Signed",  value=str(original.get("lease_signed", ""))).classes("w-full mb-2").props("outlined dense"),
                                }

                                def save_row_edit(i=idx, f=fields, r=rows_ref, rt=rt, dlg=dlg):
                                    r[i] = {
                                        "property":       f["property"].value,
                                        "unit":           f["unit"].value,
                                        "tenant":         f["tenant"].value,
                                        "rent":           f["rent"].value,
                                        "email":          f["email"].value,
                                        "lease_start":    f["lease_start"].value,
                                        "lease_end":      f["lease_end"].value,
                                        "move_in_status": f["move_in_status"].value,
                                        "banking_set_up": f["banking_set_up"].value,
                                        "lease_signed":   f["lease_signed"].value,
                                    }
                                    dlg.close()
                                    rt()
                                    ui.notify(f"Row {i + 1} updated.", type="positive")

                                with ui.row().classes("gap-2 justify-end w-full mt-2"):
                                    ui.button("Cancel", on_click=dlg.close).props("flat")
                                    ui.button("Save", on_click=save_row_edit).props("unelevated color=primary")

                            dlg.open()

                        tbl.on("edit_row", handle_edit_row)

                        # Pagination controls
                        with ui.row().classes("items-center gap-3 mt-1"):
                            prev = ui.button("← Prev", on_click=lambda sid=sid, rt=render_review_table: (
                                local_pages.update({sid: local_pages.get(sid, 1) - 1}), rt()
                            )).props("flat dense")
                            prev.set_enabled(page > 1)

                            ui.label(f"Page {page} of {total_pages} · {total} rows total").classes(
                                "text-sm"
                            ).style(f"color: {TEXT_SECONDARY}")

                            nxt = ui.button("Next →", on_click=lambda sid=sid, rt=render_review_table: (
                                local_pages.update({sid: local_pages.get(sid, 1) + 1}), rt()
                            )).props("flat dense")
                            nxt.set_enabled(page < total_pages)

                render_review_table()

            ui.separator().classes("my-4")

            # ── Approve / Reject buttons ────────────────────────────────────
            with ui.row().classes("gap-3 justify-end w-full"):

                def do_reject(sid=sub_id):
                    with ui.dialog() as dlg, ui.card().classes("p-6 w-96"):
                        ui.label("Reject Submission").classes("text-lg font-semibold mb-2")
                        note_input = ui.textarea(
                            label="Rejection note (optional)",
                            placeholder="Let the client know why this was rejected...",
                        ).classes("w-full mb-4").props("outlined autogrow")
                        with ui.row().classes("gap-2 justify-end w-full"):
                            ui.button("Cancel", on_click=dlg.close).props("flat")
                            async def confirm_reject(sid=sid, ni=note_input, dlg=dlg):
                                ok, msg = await run.io_bound(reject_submission, sid, reviewer_id, ni.value)
                                ui.notify(msg, type="positive" if ok else "negative")
                                dlg.close()
                                ui.navigate.to("/admin")
                            ui.button("Reject", on_click=confirm_reject, icon="cancel").props(
                                "unelevated color=negative"
                            )
                    dlg.open()

                def do_approve(sid=sub_id, rows=editable_rows):
                    with ui.dialog() as dlg, ui.card().classes("p-6 w-96"):
                        ui.label("Confirm Approval").classes("text-lg font-semibold mb-2")
                        ui.label(
                            f"This will import {len(rows)} row(s) into the database. "
                            "This action cannot be undone."
                        ).classes("text-sm mb-4").style(f"color: {TEXT_SECONDARY}")
                        with ui.row().classes("gap-2 justify-end w-full"):
                            ui.button("Cancel", on_click=dlg.close).props("flat")
                            async def confirm_approve(sid=sid, rows=rows, dlg=dlg):
                                ok, msg = await run.io_bound(approve_submission, sid, reviewer_id, rows_override=rows)
                                ui.notify(msg, type="positive" if ok else "negative")
                                dlg.close()
                                ui.navigate.to("/admin")
                            ui.button("Approve & Import", on_click=confirm_approve, icon="check_circle").props(
                                "unelevated color=positive"
                            )
                    dlg.open()

                ui.button("Reject", on_click=do_reject, icon="cancel").props(
                    "outline rounded color=negative"
                )
                if ftype == "spreadsheet":
                    ui.button("Approve & Import", on_click=do_approve, icon="check_circle").props(
                        "unelevated rounded color=positive"
                    )

