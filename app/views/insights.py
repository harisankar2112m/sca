import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.data import backtest, current_plan, get_ds, settings
from core.report import build_pdf

st.title("Insights & Export")
ds, cfg = get_ds(), settings()
plan = current_plan()
as_of = pd.Timestamp(ds["as_of"])
orders = plan[plan["decision"] != "No order"]
deferred = plan[plan["decision"] == "Deferred (truck limit)"]

st.subheader(f"Manager briefing — {as_of + pd.Timedelta(days=1):%A %d %B %Y}")
k = st.columns(5)
k[0].metric("Outlets at risk (Red)", int((plan["status"] == "Red").sum()))
k[1].metric("Dispatches tomorrow", int((plan["decision"] == "Dispatch today").sum()))
k[2].metric("Fuel to send", f"{plan.loc[plan['decision'] == 'Dispatch today', 'order_kL'].sum():.0f} kL")
k[3].metric("Truck trips used", f"{int(plan.loc[plan['decision'] == 'Dispatch today', 'trips'].sum())} / {cfg['trucks_per_day']}")
k[4].metric("Unserved orders", len(deferred))

by_type = plan.groupby("outlet_type").agg(red=("status", lambda s: (s == "Red").sum()), n=("status", "size"))
worst = (by_type["red"] / by_type["n"]).idxmax()
lines = []
if len(deferred):
    lines.append(f"🚨 **{len(deferred)} order(s) have no truck** with {cfg['trucks_per_day']} trips — arrange "
                 f"{int(deferred['trips'].sum())} extra trip(s): {', '.join(deferred['outlet_id'] + ' ' + deferred['product'])}.")
top = orders.sort_values("priority").head(5)
for r in top.itertuples():
    lines.append(f"{'🔴' if r.status == 'Red' else '🟠'} {r.recommendation}")
lines.append(f"📍 **{worst} outlets** carry the highest risk today ({by_type.at[worst, 'red']} of {by_type.at[worst, 'n']} "
             f"tanks in Red) — long delivery times leave less room for error.")
hsd_share = orders["order_kL"][orders["product"] == "HSD"].sum() / max(orders["order_kL"].sum(), 1)
lines.append(f"⛽ Diesel is {hsd_share:.0%} of the fuel to be dispatched — demand is running above last year (PPAC), "
             "keep the diesel surge scenario in view.")
for line in lines:
    st.markdown(line)

st.divider()
st.subheader("Does forecast-driven replenishment work? — backtest")
st.markdown("We replayed the **56-day holdout** (6 Sep – 31 Oct 2026) with the actual demand, the same depot trucks and the same "
            "random truck delays, under two policies: **current practice** (dealer indents when the tank falls below a fixed "
            "share; trucks first-come-first-served) and **DryOut Shield** (JMP forecasts → reorder points; trucks to lowest cover first).")
with st.spinner("Running backtest…"):
    bt, dates, keys = backtest(cfg["service_level"], cfg["trucks_per_day"])
a, b = bt["reactive"]["kpi"], bt["forecast"]["kpi"]
c = st.columns(4)
c[0].metric("Dry-out outlet-days", b["dry_out_outlet_days"], f"{100 * (b['dry_out_outlet_days'] / max(a['dry_out_outlet_days'], 1) - 1):+.0f}% vs {a['dry_out_outlet_days']}", delta_color="inverse")
c[1].metric("Lost sales (kL)", f"{b['lost_kL']:,.0f}", f"{100 * (b['lost_kL'] / max(a['lost_kL'], 1) - 1):+.0f}% vs {a['lost_kL']:,.0f}", delta_color="inverse")
c[2].metric("Truck trips used", f"{b['trips']:,}", f"{100 * (b['trips'] / max(a['trips'], 1) - 1):+.0f}% vs {a['trips']:,}", delta_color="inverse")
c[3].metric("Days at the truck limit", b["days_at_truck_limit"], f"{b['days_at_truck_limit'] - a['days_at_truck_limit']:+d} vs {a['days_at_truck_limit']}", delta_color="inverse")
g = go.Figure()
g.add_trace(go.Scatter(x=dates, y=bt["reactive"]["dry"].sum(0), name="Current practice", line=dict(color="#d64545")))
g.add_trace(go.Scatter(x=dates, y=bt["forecast"]["dry"].sum(0), name="DryOut Shield", line=dict(color="#2e9d5b", width=3)))
g.update_layout(height=300, margin=dict(t=20, b=10), yaxis_title="Outlet-products dry that day", legend=dict(orientation="h", y=-0.2))
st.plotly_chart(g, width="stretch")
st.caption(f"Settings: service level {cfg['service_level']:.1%}, {cfg['trucks_per_day']} trips/day (change in the sidebar). "
           "Fewer trips are needed because orders are sized to the tank's free space on arrival and placed only when the "
           "forecast says they are needed, instead of at a fixed tank level.")

st.divider()
st.subheader("Downloads")
kpis = {"Outlets in Red": int((plan["status"] == "Red").sum()), "Outlets in Amber": int((plan["status"] == "Amber").sum()),
        "Dispatches tomorrow": int((plan["decision"] == "Dispatch today").sum()),
        "Fuel to send (kL)": f"{plan.loc[plan['decision'] == 'Dispatch today', 'order_kL'].sum():.0f}",
        "Truck trips used / available": f"{int(plan.loc[plan['decision'] == 'Dispatch today', 'trips'].sum())} / {cfg['trucks_per_day']}",
        "Orders without a truck": len(deferred)}
btk = {"Dry-out outlet-days (current -> DryOut Shield)": f"{a['dry_out_outlet_days']} -> {b['dry_out_outlet_days']}",
       "Lost sales kL (current -> DryOut Shield)": f"{a['lost_kL']:,.0f} -> {b['lost_kL']:,.0f}",
       "Truck trips (current -> DryOut Shield)": f"{a['trips']:,} -> {b['trips']:,}"}
c = st.columns(4)
disp = plan[plan["decision"] == "Dispatch today"].sort_values("priority")
c[0].download_button("📄 Dispatch plan (CSV)", disp[["priority", "outlet_id", "outlet_type", "product", "order_kL", "trips",
                                                     "dispatch_date", "arrival_date", "days_of_cover", "status"]]
                     .to_csv(index=False), file_name=f"dispatch_plan_{as_of + pd.Timedelta(days=1):%Y%m%d}.csv", mime="text/csv", type="primary")
c[1].download_button("📊 Full outlet risk table (CSV)", plan.to_csv(index=False), file_name=f"outlet_risk_{as_of:%Y%m%d}.csv", mime="text/csv")
c[2].download_button("📈 28-day forecasts (CSV)", ds["forecast"].to_csv(index=False, date_format="%Y-%m-%d"),
                     file_name="forecast_28_days.csv", mime="text/csv")
c[3].download_button("🧾 Manager summary (PDF)", build_pdf(plan, kpis, cfg, as_of, ds["source"], btk),
                     file_name=f"DryOut_Shield_summary_{as_of + pd.Timedelta(days=1):%Y%m%d}.pdf", mime="application/pdf")
