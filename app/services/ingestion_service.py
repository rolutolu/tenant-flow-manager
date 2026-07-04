"""Service for importing bulk data from Excel/CSV."""
import io
import pandas as pd
from app.services.property_service import add_property, add_unit, get_properties, get_units_by_property
from app.services.tenant_service import add_tenant


def parse_file(content: bytes, filename: str) -> tuple:
    """Parse an uploaded file into a pandas DataFrame.
    Returns (df, error_str) — df is None on failure, error_str is empty on success.
    """
    try:
        fname = filename.lower()
        if fname.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        elif fname.endswith((".xls", ".xlsx")):
            df = pd.read_excel(io.BytesIO(content))
        else:
            return None, f"Unsupported file type '{filename}'. Upload a .csv, .xls, or .xlsx file."
        return df.fillna(""), ""
    except Exception as e:
        msg = str(e)
        print(f"[ERROR] parse_file failed for '{filename}': {msg}")
        return None, msg



def build_mapped_rows(df: pd.DataFrame, mapping: dict) -> list[dict]:
    """Convert a DataFrame + column mapping into a list of standardized row dicts.

    Keys in the returned dicts: property, unit, tenant, rent, email,
    lease_start, lease_end, move_in_status, banking_set_up, lease_signed.
    Rows missing required fields (property/unit/tenant) are skipped.
    """
    rows = []

    for _, row in df.iterrows():
        def get_val(key: str, default: str = "") -> str:
            col = mapping.get(key)
            if not col:
                return default
            val = row.get(col, default)
            if val is None or (isinstance(val, float) and pd.isna(val)) or val == "":
                return default
            return str(val).strip()

        p_name = get_val("Property")
        u_name = get_val("Unit")
        t_name = get_val("Tenant")

        if not p_name or not u_name or not t_name:
            continue

        rent_val = 0.0
        if mapping.get("Rent"):
            try:
                raw = row.get(mapping["Rent"], 0)
                rent_val = float(raw) if raw != "" and not (isinstance(raw, float) and pd.isna(raw)) else 0.0
            except (ValueError, TypeError):
                rent_val = 0.0

        rows.append({
            "property":       p_name,
            "unit":           u_name,
            "tenant":         t_name,
            "rent":           rent_val,
            "email":          get_val("Email"),
            "lease_start":    get_val("Lease Start"),
            "lease_end":      get_val("Lease End"),
            "move_in_status": get_val("Move-In Status", "Pending"),
            "banking_set_up": get_val("Banking Set Up", "No"),
            "lease_signed":   get_val("Lease Signed", "No"),
        })

    return rows


def execute_import(user_id: str, rows: list[dict]) -> tuple[int, int, int]:
    """Commit a list of standardized row dicts to the database.

    Creates properties, units, and tenants as needed, skipping duplicates.
    Returns (properties_created, units_created, tenants_created).
    """
    p_count, u_count, t_count = 0, 0, 0

    # Pre-load existing data to avoid redundant DB calls
    properties_cache = {p["name"]: p["id"] for p in get_properties(user_id)}
    units_cache: dict[str, dict[str, str]] = {}

    for row in rows:
        p_name = str(row.get("property", "")).strip()
        u_name = str(row.get("unit", "")).strip()
        t_name = str(row.get("tenant", "")).strip()

        if not p_name or not u_name or not t_name:
            continue

        rent_val = 0.0
        try:
            rent_val = float(row.get("rent", 0) or 0)
        except (ValueError, TypeError):
            rent_val = 0.0

        # ── Property ───────────────────────────────────────────────────────────
        if p_name not in properties_cache:
            new_p_id = add_property(user_id, p_name, address=p_name)
            if new_p_id:
                properties_cache[p_name] = new_p_id
                units_cache[new_p_id] = {}
                p_count += 1
            else:
                continue

        p_id = properties_cache[p_name]

        if p_id not in units_cache:
            units_cache[p_id] = {u["unit_number"]: u["id"] for u in get_units_by_property(p_id)}

        # ── Unit ──────────────────────────────────────────────────────────────
        if u_name not in units_cache[p_id]:
            new_u_id = add_unit(user_id, p_id, u_name, default_rent=rent_val, status="Occupied")
            if new_u_id:
                units_cache[p_id][u_name] = new_u_id
                u_count += 1
            else:
                continue

        u_id = units_cache[p_id][u_name]

        # ── Tenant ────────────────────────────────────────────────────────────
        try:
            add_tenant(
                user_id=user_id,
                name=t_name,
                unit=u_name,
                rent_amount=rent_val,
                unit_id=u_id,
                email=str(row.get("email", "") or ""),
                lease_start=str(row.get("lease_start", "") or ""),
                lease_end=str(row.get("lease_end", "") or ""),
                move_in_status=str(row.get("move_in_status", "Pending") or "Pending"),
                banking_set_up=str(row.get("banking_set_up", "No") or "No"),
                lease_signed=str(row.get("lease_signed", "No") or "No"),
            )
            t_count += 1
        except Exception as e:
            print(f"Skipped tenant {t_name}: {e}")

    return p_count, u_count, t_count


def process_bulk_import(user_id: str, df: pd.DataFrame, mapping: dict) -> tuple[int, int, int]:
    """Legacy entry point — converts DataFrame + mapping to rows then calls execute_import."""
    prop_col = mapping.get("Property")
    unit_col = mapping.get("Unit")
    tenant_col = mapping.get("Tenant")

    if not prop_col or not unit_col or not tenant_col:
        raise ValueError("Missing required mappings (Property, Unit, Tenant).")

    rows = build_mapped_rows(df, mapping)
    if not rows:
        raise ValueError("No valid rows found after applying column mappings.")

    return execute_import(user_id, rows)
