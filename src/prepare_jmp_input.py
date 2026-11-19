"""Build the modelling table that JMP uses (jmp/model_input.csv).

Data preparation done here (documented in the report, §4 Data):
  * series = outlet_id + product (60 daily series, 1 Apr 2023 - 31 Oct 2026)
  * Dry-out days: recorded sales are censored (the outlet ran out), so they
    understate demand. demand_kL replaces sales on those days with the mean
    sales of the same weekday over the previous 4 non-dry-out weeks (if that
    is higher). Normal days: demand_kL = sales_kL.
  * split: last 56 days (6 Sep - 31 Oct 2026) = Holdout, used to compare
    models in JMP; everything before = Train.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
HOLDOUT_DAYS = 56


def impute(g: pd.DataFrame) -> pd.Series:
    s = g["sales_kL"].to_numpy()
    dry = g["dry_out"].to_numpy().astype(bool)
    out = s.copy()
    for t in np.where(dry)[0]:
        lags = [t - 7 * k for k in range(1, 9) if t - 7 * k >= 0 and not dry[t - 7 * k]][:4]
        if lags:
            out[t] = max(s[t], s[lags].mean())
    return pd.Series(np.round(out, 2), index=g.index)


def main():
    s = pd.read_csv(ROOT / "data" / "outlet_daily_sales.csv", parse_dates=["date"])
    o = pd.read_csv(ROOT / "data" / "outlets.csv")
    s = s.merge(o[["outlet_id", "outlet_type"]], on="outlet_id")
    s = s.sort_values(["outlet_id", "product", "date"]).reset_index(drop=True)
    s["series"] = s["outlet_id"] + " " + s["product"]
    s["demand_kL"] = s.groupby("series", group_keys=False).apply(impute)
    cut = s["date"].max() - pd.Timedelta(days=HOLDOUT_DAYS - 1)
    s["split"] = np.where(s["date"] >= cut, "Holdout", "Train")
    cols = ["series", "outlet_id", "outlet_type", "product", "date", "sales_kL", "dry_out",
            "demand_kL", "closing_stock_kL", "split"]
    out = ROOT / "jmp" / "model_input.csv"
    out.parent.mkdir(exist_ok=True)
    s[cols].to_csv(out, index=False, date_format="%Y-%m-%d")
    print(f"{len(s):,} rows, {s.series.nunique()} series, holdout from {cut.date()}")
    print("imputed uplift on dry-out days (kL):", round((s.demand_kL - s.sales_kL).sum(), 1),
          "| true lost:", round(pd.read_csv(ROOT / "data" / "outlet_daily_sales.csv").lost_sales_kL.sum(), 1))


if __name__ == "__main__":
    main()
