import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.data import current_plan, get_ds, settings
from core.ui import STATUS_COLORS, style_status

st.title("Replenishment Planner")
ds, cfg = get_ds(), settings()
as_of = pd.Timestamp(ds["as_of"])
st.caption(f"Plan made on the evening of **{as_of:%a %d %b %Y}** for dispatch on **{as_of + pd.Timedelta(days=1):%a %d %b}** · "
           f"service level {cfg['service_level']:.1%} · depot capacity {cfg['trucks_per_day']} truck trips/day (change in sidebar)")

with st.expander("✏️ Enter today's dip readings (current stock)", expanded=False):
    st.caption("Edit the stock column with the latest dip readings; the plan updates immediately. Values above tank capacity are capped.")
    o = ds["outlets"].set_index("outlet_id")
    ed = ds["stock"][["outlet_id", "product", "current_stock_kL"]].copy()
    ed["capacity_kL"] = [o.at[r.outlet_id, f"{r.product.lower()}_capacity_kL"] for r in ed.itertuples()]
    new = st.data_editor(ed, hide_index=True, width="stretch", height=300, key="stock_editor",
                         disabled=["outlet_id", "product", "capacity_kL"],
                         column_config={"current_stock_kL": st.column_config.NumberColumn("Current stock (kL)", min_value=0.0, step=0.1, format="%.1f")})
    new["current_stock_kL"] = np.minimum(new["current_stock_kL"].fillna(0), new["capacity_kL"])
    if not np.allclose(new["current_stock_kL"].to_numpy(), ds["stock"]["current_stock_kL"].to_numpy()):
        ds["stock"] = ds["stock"].assign(current_stock_kL=new["current_stock_kL"].to_numpy())
        st.rerun()

plan = current_plan()
if plan.empty:
    st.warning("No outlets could be planned — check that stock and forecasts cover the same outlets.")
    st.stop()

orders = plan[plan["decision"] != "No order"]
deferred = plan[plan["decision"] == "Deferred (truck limit)"]
trips_needed = int(orders["trips"].sum())
k = st.columns(5)
k[0].metric("🔴 Red outlets", int((plan["status"] == "Red").sum()), help="Stock runs out before a truck dispatched tomorrow can arrive.")
k[1].metric("🟠 Amber outlets", int((plan["status"] == "Amber").sum()), help="Stock at or below the reorder point: order now.")
k[2].metric("Orders recommended", len(orders), f"{orders['order_kL'].sum():.0f} kL")
k[3].metric("Truck trips needed", trips_needed, f"{trips_needed - cfg['trucks_per_day']:+d} vs capacity",
            delta_color="inverse")
k[4].metric("Orders without a truck", len(deferred))
if len(deferred):
    st.error(f"**Truck shortage:** {len(deferred)} order(s) cannot be served with {cfg['trucks_per_day']} trips. "
             f"Most urgent unserved: {', '.join(deferred['outlet_id'] + ' ' + deferred['product'])}. "
             "Hire extra trucks or ask these dealers to ration sales.", icon="🚚")

st.subheader("Dispatch plan and outlet risk")
f1, f2, f3 = st.columns(3)
ftype = f1.multiselect("Outlet type", sorted(plan["outlet_type"].unique()), default=sorted(plan["outlet_type"].unique()))
fstat = f2.multiselect("Risk status", ["Red", "Amber", "Green"], default=["Red", "Amber", "Green"])
only = f3.toggle("Only outlets needing fuel", value=False)
view = plan[plan["outlet_type"].isin(ftype) & plan["status"].isin(fstat)]
if only:
    view = view[view["decision"] != "No order"]
cols = ["priority", "outlet_id", "outlet_type", "product", "status", "current_stock_kL", "capacity_kL", "days_of_cover",
        "avg_daily_forecast_kL", "transit_days", "reorder_point_kL", "safety_stock_kL", "dryout_prob_if_no_order",
        "order_kL", "trips", "decision", "arrival_date"]
st.dataframe(style_status(view[cols]), hide_index=True, width="stretch", height=420,
             column_config={
                 "priority": st.column_config.NumberColumn("Priority", format="%d"),
                 "days_of_cover": st.column_config.NumberColumn("Days of cover", format="%.1f"),
                 "dryout_prob_if_no_order": st.column_config.ProgressColumn("Dry-out risk if no truck", min_value=0, max_value=1, format="percent"),
                 "order_kL": st.column_config.NumberColumn("Order (kL)", format="%.0f"),
                 "avg_daily_forecast_kL": st.column_config.NumberColumn("Forecast kL/day", format="%.2f"),
             })
st.caption("**Red**: stock runs out before a truck dispatched tomorrow can arrive. **Amber**: stock at or below the reorder "
           "point – order now. **Green**: enough cover. Reorder point = dead stock + forecast demand until the next possible "
           "delivery + safety stock (z × forecast uncertainty).")

st.subheader("Outlet drill-down: projected stock")
c1, c2 = st.columns([1, 3])
sel = c1.selectbox("Outlet & product", (plan["outlet_id"] + " " + plan["product"]).tolist())
r = plan[(plan["outlet_id"] + " " + plan["product"]) == sel].iloc[0]
f = ds["forecast"]
f = f[(f["outlet_id"] == r["outlet_id"]) & (f["product"] == r["product"]) & (f["date"] > as_of)].sort_values("date").head(14)
days = f["date"].to_numpy()
d = f["forecast"].to_numpy()
no_order = np.maximum(r["current_stock_kL"] - np.cumsum(d), r["dead_stock_kL"])
with_order = no_order.copy()
if r["decision"] == "Dispatch today":
    arr = int(r["transit_days"]) - 1          # index of the arrival day in the 14-day window
    s = r["current_stock_kL"]; path = []
    for i, x in enumerate(d):
        if i == arr:
            s = min(s + r["order_kL"], r["capacity_kL"])
        s = max(s - x, r["dead_stock_kL"]); path.append(s)
    with_order = np.array(path)
c1.markdown(f"**Status:** :{'red' if r['status'] == 'Red' else 'orange' if r['status'] == 'Amber' else 'green'}[{r['status']}]")
c1.markdown(f"**Decision:** {r['decision']}")
c1.caption(r["recommendation"])
g = go.Figure()
g.add_trace(go.Scatter(x=days, y=no_order, name="No delivery", line=dict(color="#d64545", dash="dot")))
if r["decision"] == "Dispatch today":
    g.add_trace(go.Scatter(x=days, y=with_order, name=f"With {r['order_kL']:.0f} kL delivery", line=dict(color="#2e9d5b", width=3)))
g.add_hline(y=r["reorder_point_kL"], line=dict(color="#e0a100", dash="dash"), annotation_text="Reorder point")
g.add_hline(y=r["dead_stock_kL"], line=dict(color="#5b6b7b", dash="dash"), annotation_text="Dead stock (dry)")
g.add_hline(y=r["capacity_kL"], line=dict(color="#9aa5b1", width=1), annotation_text="Tank capacity")
g.update_layout(height=340, margin=dict(t=20, b=10), yaxis_title="Closing stock (kL)", legend=dict(orientation="h", y=-0.2))
c2.plotly_chart(g, width="stretch")
c2.caption("Projection uses the forecast and shows only tomorrow's dispatch; the planner re-evaluates every evening, so later orders appear in later plans.")

st.subheader("Risk map")
heat = plan.pivot_table(index="outlet_id", columns="product", values="days_of_cover").sort_index()
fig = go.Figure(go.Heatmap(z=heat.T.values, x=heat.index, y=heat.columns, zmin=0, zmax=6,
                           colorscale=[[0, STATUS_COLORS["Red"]], [0.35, STATUS_COLORS["Amber"]], [1, STATUS_COLORS["Green"]]],
                           colorbar=dict(title="Days of<br>cover"), hovertemplate="%{x} %{y}: %{z:.1f} days<extra></extra>"))
fig.update_layout(height=220, margin=dict(t=10, b=10))
st.plotly_chart(fig, width="stretch")
