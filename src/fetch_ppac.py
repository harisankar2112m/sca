"""Download PPAC monthly domestic consumption of petrol (MS) and diesel (HSD).

Source: Petroleum Planning & Analysis Cell (PPAC), Ministry of Petroleum &
Natural Gas, "Consumption - Products-wise" page
(https://ppac.gov.in/consumption/products-wise). The page loads its table
from a public JSON endpoint, one financial year (April-March) at a time.
Units are '000 metric tonnes (TMT). The latest months are provisional.

Run:  python src/fetch_ppac.py          -> writes data/ppac_monthly_ms_hsd.csv
"""
from pathlib import Path
import calendar

import pandas as pd
import requests

URL = "https://ppac.gov.in/AjaxController/getConsumptionPetroleumProductsData"
PAGE_ID = 43            # id of the products-wise consumption page
YEARS = ["2023-2024", "2024-2025", "2025-2026", "2026-2027"]
MONTHS = ["april", "may", "june", "july", "august", "september",
          "october", "november", "december", "january", "february", "march"]
# litres per kg at 15 C (typical BIS densities) used to express TMT in million litres
DENSITY = {"MS": 0.745, "HSD": 0.832}
OUT = Path(__file__).resolve().parents[1] / "data" / "ppac_monthly_ms_hsd.csv"


def fetch() -> pd.DataFrame:
    rows = []
    for fy in YEARS:
        r = requests.post(URL, data={"financialYear": fy, "reportBy": 1, "pageId": PAGE_ID},
                          headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        r.raise_for_status()
        start = int(fy[:4])
        for rec in r.json()["result"].values():
            if rec["title"] not in DENSITY:
                continue
            for i, m in enumerate(MONTHS):
                v = rec[m]
                if v in ("", None):
                    continue
                year = start if i < 9 else start + 1
                month = (i + 3) % 12 + 1
                rows.append({"month": f"{year}-{month:02d}", "financial_year": fy,
                             "product": rec["title"], "consumption_tmt": float(v),
                             "ppac_updated": rec["modified_date"]})
    df = pd.DataFrame(rows).sort_values(["product", "month"]).reset_index(drop=True)
    df["days_in_month"] = [calendar.monthrange(int(m[:4]), int(m[5:]))[1] for m in df["month"]]
    df["consumption_million_litres"] = (df["consumption_tmt"] / df["product"].map(DENSITY)).round(1)
    df["per_day_tmt"] = (df["consumption_tmt"] / df["days_in_month"]).round(2)
    return df


if __name__ == "__main__":
    df = fetch()
    OUT.parent.mkdir(exist_ok=True)
    df.to_csv(OUT, index=False)
    print(df.groupby("product")["month"].agg(["min", "max", "count"]))
    print(f"saved {OUT}")
