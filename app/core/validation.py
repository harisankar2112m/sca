"""Validation of uploaded CSV files. Each validator returns (clean_df, errors, warnings).
Errors block the upload; warnings are shown but the data is accepted."""
import pandas as pd

PRODUCTS = {"MS", "HSD"}
SALES_COLS = ["date", "outlet_id", "product", "sales_kL", "closing_stock_kL"]
OUTLET_COLS = ["outlet_id", "outlet_type", "distance_km", "transit_days", "ms_capacity_kL",
               "hsd_capacity_kL", "ms_dead_stock_kL", "hsd_dead_stock_kL"]
STOCK_COLS = ["outlet_id", "product", "current_stock_kL", "as_of_date"]
MIN_DAYS = 730          # 2 years: seasonal models need repeated weekly + annual cycles
MAX_ROWS = 500_000


def _read(file) -> tuple[pd.DataFrame | None, list[str]]:
    try:
        df = pd.read_csv(file)
    except Exception as e:  # noqa: BLE001 - show any parse error to the user
        return None, [f"Could not read the file as CSV ({e}). Save it as comma-separated UTF-8 and try again."]
    if df.empty:
        return None, ["The file has no data rows."]
    df.columns = [c.strip() for c in df.columns]
    return df, []


def _missing_cols(df, cols):
    miss = [c for c in cols if c not in df.columns]
    return [f"Missing required column(s): {', '.join(miss)}. Download the template to see the expected format."] if miss else []


def _numeric(df, cols, errors, nonneg=True):
    for c in cols:
        v = pd.to_numeric(df[c], errors="coerce")
        bad = v.isna() & df[c].notna()
        if bad.any():
            errors.append(f"Column '{c}' has {bad.sum()} non-numeric value(s), e.g. row {bad.idxmax() + 2}.")
        if nonneg and (v < 0).any():
            errors.append(f"Column '{c}' has {(v < 0).sum()} negative value(s), e.g. row {(v < 0).idxmax() + 2}.")
        df[c] = v
    return df


def validate_sales(file):
    df, errors = _read(file)
    warnings = []
    if df is None:
        return None, errors, warnings
    errors += _missing_cols(df, SALES_COLS)
    if errors:
        return None, errors, warnings
    if len(df) > MAX_ROWS:
        return None, [f"File has {len(df):,} rows; the limit is {MAX_ROWS:,}."], warnings
    df = df[SALES_COLS].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if df["date"].isna().any():
        errors.append(f"{df['date'].isna().sum()} row(s) have an invalid date (use YYYY-MM-DD).")
    df["product"] = df["product"].astype(str).str.strip().str.upper()
    badp = ~df["product"].isin(PRODUCTS)
    if badp.any():
        errors.append(f"'product' must be MS or HSD; found {sorted(map(str, df.loc[badp, 'product'].unique()))[:5]}.")
    df["outlet_id"] = df["outlet_id"].astype(str).str.strip()
    df = _numeric(df, ["sales_kL", "closing_stock_kL"], errors)
    miss = df[["sales_kL"]].isna().sum().sum()
    if miss:
        errors.append(f"{miss} missing sales value(s). Fill them (0 if the outlet was closed).")
    if errors:
        return None, errors, warnings
    dup = df.duplicated(["date", "outlet_id", "product"])
    if dup.any():
        errors.append(f"{dup.sum()} duplicate date × outlet × product row(s).")
        return None, errors, warnings
    span = df.groupby(["outlet_id", "product"])["date"].agg(["min", "max", "count"])
    short = span[(span["max"] - span["min"]).dt.days + 1 < MIN_DAYS]
    if len(short) == len(span):
        errors.append(f"Every series has less than {MIN_DAYS} days of history; at least 2 years is needed.")
        return None, errors, warnings
    if len(short):
        warnings.append(f"{len(short)} series have under 2 years of history and were dropped: "
                        f"{', '.join(a + ' ' + b for a, b in short.index[:6])}{'…' if len(short) > 6 else ''}")
        keep = ~df.set_index(["outlet_id", "product"]).index.isin(short.index)
        df = df[keep]
    gaps = span["count"] < (span["max"] - span["min"]).dt.days + 1
    if gaps.any():
        warnings.append(f"{gaps.sum()} series have missing days; gaps are filled by carrying the weekly pattern.")
    if (df["closing_stock_kL"].isna()).any():
        warnings.append("Some closing stock values are blank; dry-out days cannot be detected for those rows.")
    return df.sort_values(["outlet_id", "product", "date"]).reset_index(drop=True), errors, warnings


def validate_outlets(file):
    df, errors = _read(file)
    warnings = []
    if df is None:
        return None, errors, warnings
    errors += _missing_cols(df, OUTLET_COLS)
    if errors:
        return None, errors, warnings
    df = df[OUTLET_COLS].copy()
    df["outlet_id"] = df["outlet_id"].astype(str).str.strip()
    if df["outlet_id"].duplicated().any():
        errors.append("Duplicate outlet_id values in the outlet file.")
    num = OUTLET_COLS[2:]
    df = _numeric(df, num, errors)
    if df[num].isna().any().any():
        errors.append("Outlet file has blank numeric values.")
    if errors:
        return None, errors, warnings
    for p in ("ms", "hsd"):
        bad = df[f"{p}_dead_stock_kL"] >= df[f"{p}_capacity_kL"]
        if bad.any():
            errors.append(f"{p.upper()} dead stock must be below tank capacity (outlets {', '.join(df.loc[bad, 'outlet_id'])}).")
    if (df["transit_days"] < 1).any() or (df["transit_days"] > 10).any():
        errors.append("transit_days must be between 1 and 10.")
    if errors:
        return None, errors, warnings
    df["transit_days"] = df["transit_days"].astype(int)
    return df, errors, warnings


def validate_stock(file, outlets: pd.DataFrame):
    df, errors = _read(file)
    warnings = []
    if df is None:
        return None, errors, warnings
    errors += _missing_cols(df, STOCK_COLS)
    if errors:
        return None, errors, warnings
    df = df[STOCK_COLS].copy()
    df["outlet_id"] = df["outlet_id"].astype(str).str.strip()
    df["product"] = df["product"].astype(str).str.strip().str.upper()
    if (~df["product"].isin(PRODUCTS)).any():
        errors.append("'product' must be MS or HSD.")
    df = _numeric(df, ["current_stock_kL"], errors)
    df["as_of_date"] = pd.to_datetime(df["as_of_date"], errors="coerce")
    if df["as_of_date"].isna().any():
        errors.append("Invalid as_of_date (use YYYY-MM-DD).")
    unknown = set(df["outlet_id"]) - set(outlets["outlet_id"])
    if unknown:
        errors.append(f"Unknown outlet_id(s) not in the outlet master: {', '.join(sorted(unknown)[:8])}.")
    if errors:
        return None, errors, warnings
    o = outlets.set_index("outlet_id")
    cap = [o.at[r.outlet_id, f"{r.product.lower()}_capacity_kL"] for r in df.itertuples()]
    over = df["current_stock_kL"].to_numpy() > pd.Series(cap).to_numpy() + 1e-6
    if over.any():
        errors.append(f"{over.sum()} row(s) have stock above tank capacity.")
        return None, errors, warnings
    if df.duplicated(["outlet_id", "product"]).any():
        errors.append("Duplicate outlet × product rows.")
        return None, errors, warnings
    return df, errors, warnings
