"""Data Ingestion page — dual upload paths.

Path A (Spreadsheet): .csv / .xlsx / .xls
  Upload → map columns (10 fields) → paginated preview → Submit for Approval
  Nothing hits the tenants table until the superadmin approves.

Path B (Raw file): anything else (.db, .sqlite, .sql, .pdf, .png, images, .zip, etc.)
  One-click upload → file saved to Supabase Storage for manual review.
"""

import math
from nicegui import ui, run
from app.auth import require_role, get_user_id
from app.theme import (
    page_layout, section_header,
    ACCENT, TEXT_SECONDARY, SUCCESS, DANGER, WARNING, CARD_BG, BORDER,
)
from app.services.ingestion_service import parse_file, build_mapped_rows
from app.services.import_submission_service import (
    submit_spreadsheet, submit_raw_file, get_user_submissions,
)
from app.services.rate_limit_service import check_rate_limit, record_attempt

# ── Constants ──────────────────────────────────────────────────────────────────

SPREADSHEET_EXTS = {".csv", ".xlsx", ".xls"}
ROWS_PER_PAGE = 50

REQUIRED_FIELDS = ["Property", "Unit", "Tenant"]
OPTIONAL_FIELDS = ["Rent", "Email", "Lease Start", "Lease End",
                   "Move-In Status", "Banking Set Up", "Lease Signed"]
ALL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS

PREVIEW_COLUMNS = [
    {"name": "n",             "label": "#",          "field": "n",             "align": "right"},
    {"name": "property",      "label": "Property",   "field": "property",      "align": "left"},
    {"name": "unit",          "label": "Unit",        "field": "unit",          "align": "left"},
    {"name": "tenant",        "label": "Tenant",      "field": "tenant",        "align": "left"},
    {"name": "rent",          "label": "Rent",        "field": "rent",          "align": "right"},
    {"name": "email",         "label": "Email",       "field": "email",         "align": "left"},
    {"name": "lease_start",   "label": "Lease Start", "field": "lease_start",   "align": "left"},
    {"name": "lease_end",     "label": "Lease End",   "field": "lease_end",     "align": "left"},
    {"name": "move_in_status","label": "Move-In",     "field": "move_in_status","align": "left"},
    {"name": "banking_set_up","label": "Banking",     "field": "banking_set_up","align": "left"},
    {"name": "lease_signed",  "label": "Signed",      "field": "lease_signed",  "align": "left"},
]


# ── Page ───────────────────────────────────────────────────────────────────────

@ui.page("/import")
@require_role("admin", "manager")
async def import_page():
    user_id = get_user_id()

    # ── Spreadsheet state ──────────────────────────────────────────────────────
    ss = {
        "df":          None,
        "filename":    "",
        "file_bytes":  b"",
        "columns":     [],
        "mapping":     {f: None for f in ALL_FIELDS},
        "mapped_rows": [],
        "page":        1,
        "submitted":   False,
    }

    with page_layout(title="Data Ingestion"):
        section_header(
            "Bulk Data Import",
            "Upload a spreadsheet for approval, or send any file directly to Virix for manual review",
        )

        with ui.tabs().classes("w-full mb-6") as tabs:
            ui.tab("sheet", label="📊  Spreadsheet")
            ui.tab("raw",   label="📁  Documents & Files")

        with ui.tab_panels(tabs, value="sheet").classes("w-full"):

            # ══════════════════════════════════════════════════════════════════
            # PATH A — Spreadsheet
            # ══════════════════════════════════════════════════════════════════
            with ui.tab_panel("sheet"):

                # ── Upload card ───────────────────────────────────────────────
                with ui.card().classes("w-full p-6 mb-4 shadow-sm").style(
                    f"background: {CARD_BG}; border: 1px solid {BORDER}"
                ):
                    ui.label("1  ·  Upload Spreadsheet").classes("text-lg font-bold mb-1")
                    ui.label("Accepts .csv, .xlsx, or .xls files.").classes("text-sm mb-4").style(
                        f"color: {TEXT_SECONDARY}"
                    )

                    mapper_area   = ui.column().classes("w-full gap-4")
                    preview_area  = ui.column().classes("w-full gap-2")
                    confirm_area  = ui.column().classes("w-full")

                    # ── Helpers ───────────────────────────────────────────────

                    def render_preview():
                        preview_area.clear()
                        rows = ss["mapped_rows"]
                        if not rows:
                            return

                        total = len(rows)
                        page  = ss["page"]
                        total_pages = max(1, math.ceil(total / ROWS_PER_PAGE))
                        page  = max(1, min(page, total_pages))
                        ss["page"] = page

                        start = (page - 1) * ROWS_PER_PAGE
                        end   = min(start + ROWS_PER_PAGE, total)
                        page_rows = [
                            {"n": start + i + 1, **r}
                            for i, r in enumerate(rows[start:end])
                        ]

                        with preview_area:
                            with ui.card().classes("w-full p-6 shadow-sm").style(
                                f"background: {CARD_BG}; border: 1px solid {BORDER}"
                            ):
                                with ui.row().classes("items-center justify-between w-full mb-3"):
                                    ui.label("3  ·  Preview").classes("text-lg font-bold")
                                    ui.label(
                                        f"Rows {start + 1}–{end} of {total}"
                                    ).classes("text-sm").style(f"color: {TEXT_SECONDARY}")

                                ui.table(columns=PREVIEW_COLUMNS, rows=page_rows).classes(
                                    "w-full"
                                ).props("flat dense bordered")

                                with ui.row().classes("items-center gap-3 mt-3 justify-between w-full"):
                                    with ui.row().classes("gap-2"):
                                        prev_btn = ui.button(
                                            "← Prev",
                                            on_click=lambda: _go_page(-1),
                                        ).props("flat dense")
                                        prev_btn.set_enabled(page > 1)

                                        ui.label(f"Page {page} of {total_pages}").classes(
                                            "text-sm self-center"
                                        )

                                        next_btn = ui.button(
                                            "Next →",
                                            on_click=lambda: _go_page(1),
                                        ).props("flat dense")
                                        next_btn.set_enabled(page < total_pages)

                                    ui.button(
                                        "Submit for Approval",
                                        on_click=handle_submit,
                                        icon="send",
                                    ).props("unelevated rounded").style(
                                        f"background: linear-gradient(135deg, {ACCENT}, #3A3A3A) !important; color: white !important;"
                                    )

                    def _go_page(delta: int):
                        ss["page"] += delta
                        render_preview()

                    def render_mapper():
                        mapper_area.clear()
                        if ss["df"] is None:
                            return
                        cols = ss["columns"]

                        with mapper_area:
                            with ui.card().classes("w-full p-6 shadow-sm").style(
                                f"background: {CARD_BG}; border: 1px solid {BORDER}"
                            ):
                                ui.label(
                                    f"2  ·  Map Columns  —  \"{ss['filename']}\""
                                ).classes("text-lg font-bold mb-1")
                                ui.label(
                                    "Tell Virix which columns in your sheet map to each field. "
                                    "Required fields are marked ✱."
                                ).classes("text-sm mb-4").style(f"color: {TEXT_SECONDARY}")

                                # Required row
                                ui.label("Required").classes(
                                    "text-xs font-bold tracking-widest uppercase mb-2"
                                ).style(f"color: {TEXT_SECONDARY}")
                                with ui.row().classes("w-full gap-4 flex-wrap mb-4"):
                                    for field in REQUIRED_FIELDS:
                                        ui.select(
                                            label=f"{field} ✱",
                                            options=cols,
                                            value=ss["mapping"].get(field),
                                            on_change=lambda e, f=field: _on_map(f, e.value),
                                        ).classes("flex-1 min-w-[200px]").props("outlined")

                                # Optional row
                                ui.label("Optional").classes(
                                    "text-xs font-bold tracking-widest uppercase mb-2"
                                ).style(f"color: {TEXT_SECONDARY}")
                                with ui.row().classes("w-full gap-4 flex-wrap"):
                                    for field in OPTIONAL_FIELDS:
                                        ui.select(
                                            label=field,
                                            options=["(none)"] + cols,
                                            value=ss["mapping"].get(field) or "(none)",
                                            on_change=lambda e, f=field: _on_map(
                                                f, None if e.value == "(none)" else e.value
                                            ),
                                        ).classes("flex-1 min-w-[200px]").props("outlined clearable")

                                ui.button(
                                    "Build Preview",
                                    on_click=handle_build_preview,
                                    icon="table_view",
                                ).classes("mt-4").props("unelevated color=primary")

                    def _on_map(field: str, value):
                        ss["mapping"][field] = value

                    def handle_build_preview():
                        required_ok = all(ss["mapping"].get(f) for f in REQUIRED_FIELDS)
                        if not required_ok:
                            ui.notify(
                                "Please map all three required fields (Property, Unit, Tenant).",
                                type="warning",
                            )
                            return
                        rows = build_mapped_rows(ss["df"], ss["mapping"])
                        if not rows:
                            ui.notify("No valid rows found after mapping. Check your column selections.", type="negative")
                            return
                        ss["mapped_rows"] = rows
                        ss["page"] = 1
                        render_preview()
                        ui.notify(f"{len(rows)} rows ready for review.", type="positive")

                    async def handle_submit():
                        if not ss["mapped_rows"]:
                            ui.notify("Build the preview first.", type="warning")
                            return
                        ui.notify("Submitting…", type="info")
                        sub_id = await run.io_bound(
                            submit_spreadsheet,
                            user_id,
                            ss["filename"],
                            ss["file_bytes"],
                            {k: v for k, v in ss["mapping"].items() if v},
                            ss["mapped_rows"],
                        )
                        if sub_id:
                            ss["submitted"] = True
                            mapper_area.clear()
                            preview_area.clear()
                            _show_confirm(sub_id)
                        else:
                            ui.notify("Submission failed — please try again.", type="negative")

                    def _show_confirm(sub_id: str):
                        confirm_area.clear()
                        with confirm_area:
                            with ui.card().classes("w-full p-8 items-center text-center shadow-sm").style(
                                f"background: {CARD_BG}; border: 1px solid {BORDER}"
                            ):
                                ui.icon("check_circle", size="56px").style(f"color: {SUCCESS}")
                                ui.label("Submitted for Review").classes(
                                    "text-2xl font-bold mt-3"
                                ).style("color: #1C1915")
                                ui.label(
                                    f"Your file ({ss['filename']}, {len(ss['mapped_rows'])} rows) "
                                    "is pending review by Virix. Your data will not appear in the "
                                    "system until it has been approved."
                                ).classes("text-sm mt-2 max-w-md").style(f"color: {TEXT_SECONDARY}")
                                ui.button(
                                    "Submit Another File",
                                    on_click=lambda: ui.navigate.to("/import"),
                                    icon="upload_file",
                                ).classes("mt-6").props("outline rounded")

                    def _show_fallback(filename: str, file_bytes: bytes, error_msg: str):
                        confirm_area.clear()
                        mapper_area.clear()
                        preview_area.clear()
                        with confirm_area:
                            with ui.card().classes("w-full p-6 shadow-sm rounded-xl").style(
                                f"background: {CARD_BG}; border: 1px solid #FFE4E6"  # soft rose border
                            ):
                                with ui.row().classes("items-center gap-3 mb-2"):
                                    ui.icon("warning", size="28px").style("color: #F43F5E")
                                    ui.label("Auto-Parsing Failed").classes("text-lg font-bold").style("color: #9F1239")
                                
                                ui.label(
                                    f"We couldn't parse '{filename}' automatically: {error_msg or 'No rows found.'}"
                                ).classes("text-sm mb-3").style(f"color: {TEXT_SECONDARY}")
                                
                                ui.label(
                                    "Would you like to send this file directly to Virix for manual review and import instead?"
                                ).classes("text-sm mb-5 font-medium")
                                
                                async def handle_fallback_submit():
                                    ui.notify("Submitting for manual import...", type="info")
                                    sub_id = await run.io_bound(submit_raw_file, user_id, filename, file_bytes)
                                    if sub_id:
                                        confirm_area.clear()
                                        with confirm_area:
                                            with ui.card().classes("w-full p-8 items-center text-center shadow-sm").style(
                                                f"background: {CARD_BG}; border: 1px solid {BORDER}"
                                            ):
                                                ui.icon("cloud_done", size="56px").style(f"color: {SUCCESS}")
                                                ui.label("File Submitted for Manual Review").classes("text-2xl font-bold mt-3")
                                                ui.label(
                                                    f"'{filename}' has been sent to Virix. "
                                                    "Our team will manually review and import your data shortly."
                                                ).classes("text-sm mt-2 max-w-md").style(f"color: {TEXT_SECONDARY}")
                                                ui.button(
                                                    "Submit Another File",
                                                    on_click=lambda: ui.navigate.to("/import"),
                                                    icon="upload_file",
                                                ).classes("mt-6").props("outline rounded")
                                    else:
                                        ui.notify("Failed to submit file for manual review.", type="negative")

                                with ui.row().classes("gap-3"):
                                    ui.button(
                                        "Submit for Manual Import", 
                                        on_click=handle_fallback_submit,
                                        icon="forward_to_inbox"
                                    ).props("unelevated rounded")
                                    ui.button(
                                        "Try Another File", 
                                        on_click=lambda: ui.navigate.to("/import"),
                                        icon="replay"
                                    ).props("outline rounded color=grey")

                    # ── Upload widget ─────────────────────────────────────────
                    async def handle_upload(e):
                        name = "data.csv"
                        content = b""
                        try:
                            # Rate limiting: limit to 10 uploads per 10 minutes per user
                            user_key = f"upload_user:{user_id}"
                            ok, retry_after = check_rate_limit(user_key, 10, 600)
                            if not ok:
                                ui.notify(f"Upload rate limit exceeded. Please wait {retry_after} seconds.", type="negative")
                                return

                            record_attempt(user_key)
                            name = getattr(e.file, "name", None) or getattr(e.file, "filename", None) or "data.csv"
                            content = await e.file.read()

                            if not content:
                                ui.notify("File is empty — please check the file and try again.", type="negative")
                                return

                            df, parse_err = await run.io_bound(parse_file, content, name)
                            if df is None or df.empty:
                                _show_fallback(name, content, parse_err)
                                return

                            ss.update({
                                "df":          df,
                                "filename":    name,
                                "file_bytes":  content,
                                "columns":     df.columns.tolist(),
                                "mapped_rows": [],
                                "page":        1,
                                "submitted":   False,
                            })

                            # Auto-guess column mappings from header names
                            for col in ss["columns"]:
                                cl = col.lower()
                                if any(k in cl for k in ("prop", "build", "complex")):
                                    ss["mapping"]["Property"] = ss["mapping"]["Property"] or col
                                elif any(k in cl for k in ("unit", "apt", "suite")):
                                    ss["mapping"]["Unit"] = ss["mapping"]["Unit"] or col
                                elif any(k in cl for k in ("name", "tenant", "renter")):
                                    ss["mapping"]["Tenant"] = ss["mapping"]["Tenant"] or col
                                elif any(k in cl for k in ("rent", "amount", "monthly")):
                                    ss["mapping"]["Rent"] = ss["mapping"]["Rent"] or col
                                elif "email" in cl:
                                    ss["mapping"]["Email"] = ss["mapping"]["Email"] or col
                                elif any(k in cl for k in ("start", "from", "begin")):
                                    ss["mapping"]["Lease Start"] = ss["mapping"]["Lease Start"] or col
                                elif any(k in cl for k in ("end", "expir", "until")):
                                    ss["mapping"]["Lease End"] = ss["mapping"]["Lease End"] or col

                            confirm_area.clear()
                            preview_area.clear()
                            render_mapper()
                            ui.notify(
                                f"Parsed {len(df)} rows from {name}. Map your columns below.",
                                type="positive",
                            )
                        except Exception as err:
                            _show_fallback(name, content, str(err))

                    ui.upload(
                        label="Drag & Drop .csv or .xlsx",
                        auto_upload=True,
                        on_upload=handle_upload,
                        max_files=1,
                    ).classes("w-full max-w-lg").props('accept=".csv,.xlsx,.xls"')

                # ── Mapper / Preview / Confirm rendered below the upload card ──

            # ══════════════════════════════════════════════════════════════════
            # PATH B — Raw files
            # ══════════════════════════════════════════════════════════════════
            with ui.tab_panel("raw"):

                with ui.card().classes("w-full p-6 shadow-sm").style(
                    f"background: {CARD_BG}; border: 1px solid {BORDER}"
                ):
                    ui.label("Upload Any File to Virix").classes("text-lg font-bold mb-1")
                    ui.label(
                        "Send a database export, image, PDF, or any other file. "
                        "Virix will receive it in Supabase and manually import your data."
                    ).classes("text-sm mb-2").style(f"color: {TEXT_SECONDARY}")

                    with ui.card().classes("w-full p-4 mb-4 rounded-xl").style(
                        "background: #F8FAFC; border: 1px solid #E2E8F0"
                    ):
                        ui.label("Supported formats (non-exhaustive)").classes(
                            "text-xs font-bold tracking-wider mb-2"
                        ).style(f"color: {TEXT_SECONDARY}")
                        ui.label(
                            ".db  ·  .sqlite  ·  .sql  ·  .pdf  ·  .png / .jpg  ·  "
                            ".zip  ·  .json  ·  .txt  ·  .docx  ·  .ods  ·  and more"
                        ).classes("text-xs").style(f"color: {TEXT_SECONDARY}")

                    raw_status = ui.column().classes("w-full mt-2")

                    async def handle_raw_upload(e):
                        try:
                            # Rate limiting: limit to 10 uploads per 10 minutes per user
                            user_key = f"upload_user:{user_id}"
                            ok, retry_after = check_rate_limit(user_key, 10, 600)
                            if not ok:
                                ui.notify(f"Upload rate limit exceeded. Please wait {retry_after} seconds.", type="negative")
                                return

                            record_attempt(user_key)
                            name = getattr(e.file, "name", None) or getattr(e.file, "filename", None) or "upload"
                            content = await e.file.read()
                            sub_id = await run.io_bound(submit_raw_file, user_id, name, content)
                            raw_status.clear()
                            with raw_status:
                                if sub_id:
                                    with ui.card().classes("w-full p-6 items-center text-center").style(
                                        f"background: {CARD_BG}; border: 1px solid {BORDER}"
                                    ):
                                        ui.icon("cloud_done", size="40px").style(f"color: {SUCCESS}")
                                        ui.label("File Uploaded").classes("text-lg font-bold mt-2")
                                        ui.label(
                                            f"\"{name}\" has been delivered to Virix. "
                                            "Your data will be imported manually and you will be notified."
                                        ).classes("text-sm mt-1").style(f"color: {TEXT_SECONDARY}")
                                else:
                                    ui.label("Upload failed — please try again.").style(
                                        f"color: {DANGER}"
                                    )
                        except Exception as err:
                            ui.notify(f"Upload error: {str(err)}", type="negative")

                    ui.upload(
                        label="Drag & Drop Any File",
                        auto_upload=True,
                        on_upload=handle_raw_upload,
                        max_files=1,
                    ).classes("w-full max-w-lg").props(
                        'accept=".db,.sqlite,.sql,.pdf,.png,.jpg,.jpeg,.gif,.webp,.bmp,'
                        '.zip,.tar,.gz,.json,.txt,.docx,.ods,.pptx,.xml,.csv,.tsv"'
                    )

        # ── Submission history ─────────────────────────────────────────────────
        history = await run.io_bound(get_user_submissions, user_id)
        if history:
            section_header("Your Submission History", "Past imports and their review status")
            rows = [
                {
                    "filename":     s["filename"],
                    "type":         s["file_type"].capitalize(),
                    "rows":         s.get("row_count", 0),
                    "status":       s["status"].capitalize(),
                    "date":         (s.get("submitted_at") or "")[:10],
                    "note":         s.get("rejection_note", "") or "",
                }
                for s in history
            ]
            ui.table(
                columns=[
                    {"name": "date",     "label": "Date",     "field": "date",     "align": "left"},
                    {"name": "filename", "label": "File",     "field": "filename", "align": "left"},
                    {"name": "type",     "label": "Type",     "field": "type",     "align": "left"},
                    {"name": "rows",     "label": "Rows",     "field": "rows",     "align": "right"},
                    {"name": "status",   "label": "Status",   "field": "status",   "align": "left"},
                    {"name": "note",     "label": "Note",     "field": "note",     "align": "left"},
                ],
                rows=rows,
            ).classes("w-full").props("flat bordered dense")
