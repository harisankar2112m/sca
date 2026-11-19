"""PDF summary of the dispatch plan for the depot manager (fpdf2, core fonts)."""
from datetime import datetime

import pandas as pd
from fpdf import FPDF


def _t(s) -> str:
    """Core PDF fonts are Latin-1: replace characters they cannot draw."""
    s = str(s).replace("–", "-").replace("—", "-").replace("×", "x").replace("₹", "Rs ").replace("≤", "<=")
    return s.encode("latin-1", "replace").decode("latin-1")


def build_pdf(plan: pd.DataFrame, kpis: dict, settings: dict, as_of, source: str, backtest: dict | None = None) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(True, margin=14)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 9, _t("DryOut Shield - Daily Dispatch Summary"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, _t(f"Stock as of {pd.Timestamp(as_of).date()} | dispatch day {(pd.Timestamp(as_of) + pd.Timedelta(days=1)).date()} | "
                            f"generated {datetime.now():%Y-%m-%d %H:%M}\nData: {source}\n"
                            f"Settings: service level {settings['service_level']:.0%}, depot trucks {settings['trucks_per_day']} trips/day"))
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Key figures", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for k, v in kpis.items():
        pdf.cell(80, 6, _t(k)); pdf.cell(0, 6, _t(v), new_x="LMARGIN", new_y="NEXT")
    if backtest:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Policy backtest (56-day holdout, same trucks)", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        for k, v in backtest.items():
            pdf.cell(80, 6, _t(k)); pdf.cell(0, 6, _t(v), new_x="LMARGIN", new_y="NEXT")

    act = plan[plan["decision"] != "No order"].sort_values("priority")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, f"Dispatch list ({len(act)} orders)", new_x="LMARGIN", new_y="NEXT")
    cols = [("priority", "#", 8), ("outlet_id", "Outlet", 16), ("product", "Prod", 12), ("status", "Risk", 14),
            ("current_stock_kL", "Stock kL", 18), ("days_of_cover", "Cover d", 16), ("reorder_point_kL", "ROP kL", 16),
            ("order_kL", "Order kL", 17), ("trips", "Trips", 12), ("decision", "Decision", 40)]
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(230, 230, 230)
    for _, h, w in cols:
        pdf.cell(w, 6, h, border=1, fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    colours = {"Red": (250, 215, 215), "Amber": (252, 236, 200), "Green": (220, 240, 220)}
    for r in act.itertuples():
        pdf.set_fill_color(*colours.get(r.status, (255, 255, 255)))
        for c, _, w in cols:
            v = getattr(r, c)
            v = "" if v is None or (isinstance(v, float) and pd.isna(v)) else (f"{v:.0f}" if c in ("priority",) else v)
            pdf.cell(w, 5.5, _t(v), border=1, fill=(c == "status"))
        pdf.ln()

    alerts = plan[plan["decision"] == "Deferred (truck limit)"]
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Alerts and recommendations", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    lines = list(alerts["recommendation"]) + list(act[act["decision"] == "Dispatch today"]["recommendation"].head(10))
    if not lines:
        lines = ["No outlet needs fuel today."]
    for s in lines:
        pdf.multi_cell(0, 5, _t("- " + s), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _t("Method: daily demand forecasts from JMP Time Series Forecast (ETS models, AIC-selected, weekly season); "
                            "safety stock = z x forecast sd over the delivery window; reorder point = dead stock + forecast demand "
                            "over the window + safety stock; orders in 4 kL compartments; trucks allocated by lowest days of cover. "
                            "Outlet data is synthetic (calibrated to PPAC); decisions should be checked against actual dip readings."))
    return bytes(pdf.output())
