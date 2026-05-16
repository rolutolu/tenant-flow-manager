"""Service for importing bulk data from Excel/CSV."""
import pandas as pd
import io
from app.services.property_service import add_property, add_unit, get_properties, get_units_by_property
from app.services.tenant_service import add_tenant

def parse_file(content: bytes, filename: str) -> pd.DataFrame | None:
    """Parse an uploaded file into a pandas DataFrame."""
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        elif filename.endswith((".xls", ".xlsx")):
            df = pd.read_excel(io.BytesIO(content))
        else:
            return None
        return df.fillna("")
    except Exception as e:
        print(f"Error parsing file: {e}")
        return None

def process_bulk_import(user_id: str, df: pd.DataFrame, mapping: dict) -> tuple[int, int, int]:
    """
    Process mapped dataframe to create properties, units, and tenants.
    Mapping looks like: {"Property": "Building Name Col", "Unit": "Apt Col", "Tenant": "Name Col", "Rent": "Rent Col"}
    Returns (properties_created, units_created, tenants_created)
    """
    prop_col = mapping.get("Property")
    unit_col = mapping.get("Unit")
    tenant_col = mapping.get("Tenant")
    rent_col = mapping.get("Rent")

    if not prop_col or not unit_col or not tenant_col:
        raise ValueError("Missing required mappings (Property, Unit, Tenant).")

    p_count, u_count, t_count = 0, 0, 0
    
    # Cache to avoid duplicate DB calls
    properties_cache = {p["name"]: p["id"] for p in get_properties(user_id)}
    units_cache = {}

    for _, row in df.iterrows():
        p_name = str(row[prop_col]).strip()
        u_name = str(row[unit_col]).strip()
        t_name = str(row[tenant_col]).strip()
        rent_val = row[rent_col] if rent_col and row[rent_col] else 0
        try:
            rent_val = float(rent_val)
        except ValueError:
            rent_val = 0.0

        if not p_name or not u_name or not t_name:
            continue

        # 1. Handle Property
        if p_name not in properties_cache:
            new_p_id = add_property(user_id, p_name, address=p_name) # Default address to name
            if new_p_id:
                properties_cache[p_name] = new_p_id
                units_cache[new_p_id] = {}
                p_count += 1
            else:
                continue
        
        p_id = properties_cache[p_name]

        # Populate unit cache for this property if not done
        if p_id not in units_cache:
            units_cache[p_id] = {u["unit_number"]: u["id"] for u in get_units_by_property(p_id)}

        # 2. Handle Unit
        if u_name not in units_cache[p_id]:
            new_u_id = add_unit(user_id, p_id, u_name, default_rent=rent_val, status="Occupied")
            if new_u_id:
                units_cache[p_id][u_name] = new_u_id
                u_count += 1
            else:
                continue

        u_id = units_cache[p_id][u_name]

        # 3. Handle Tenant
        try:
            # Note: We pass unit_id to the modified add_tenant
            add_tenant(user_id=user_id, name=t_name, unit=u_name, rent_amount=rent_val, unit_id=u_id)
            t_count += 1
        except Exception as e:
            print(f"Skipped tenant {t_name}: {e}")

    return p_count, u_count, t_count
