import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.data import current_plan, get_ds, scenario_sim, settings

st.title("Scenarios")
ds, cfg = get_ds(), settings()
st.markdown("Stress-test tomorrow's plan and the next **28 days** under demand surges, delivery delays and truck shortages. "
            "The 28-day results simulate the forecast-driven policy day by day over 10 random demand paths.")

PRESETS = {
    "Custom": None,
    "Diesel price-gap surge (+25% demand)": dict(uplift=25, delay=0, trucks=cfg["trucks_per_day"]),
    "Festival rush (+15% demand)": dict(uplift=15, delay=0, trucks=cfg["trucks_per_day"]),
    "Transporters' strike (+2 days delay, 30% fewer trucks)": dict(uplift=10, delay=2, trucks=int(cfg["trucks_per_day"] * 0.7)),
    "Fleet cut (25% fewer trucks)": dict(uplift=0, delay=0, trucks=int(cfg["trucks_per_day"] * 0.75)),
}
st.session_state.setdefault("sc_uplift", 0)
st.session_state.setdefault("sc_delay", 0)
st.session_state.setdefault("sc_trucks", cfg["trucks_per_day"])
st.session_state.setdefault("sc_sl", cfg["service_level"])


def apply_preset():
    p = PRESETS[st.session_state.sc_preset]
    if p:
        st.session_state.sc_uplift, st.session_state.sc_delay, st.session_state.sc_trucks = p["uplift"], p["delay"], p["trucks"]


c = st.columns([2, 1, 1, 1, 1])
c[0].selectbox("Preset", list(PRESETS), key="sc_preset", on_change=apply_preset)
c[1].slider("Demand change (%)", -20, 50, step=5, key="sc_uplift")
c[2].slider("Extra delivery delay (days)", 0, 4, key="sc_delay")
c[3].number_input("Truck trips/day", 5, 100, key="sc_trucks")
c[4].select_slider("Service level", [0.90, 0.95, 0.98, 0.99, 0.995], key="sc_sl", format_func=lambda v: f"{v:.1%}")
aware = st.toggle("Planner anticipates the demand change (adjusts forecasts)", value=True,
                  help="On: the manager knows about the surge and raises the forecast. Off: the surge comes as a surprise.")

up, dl, tk, sl = st.session_state.sc_uplift / 100, st.session_state.sc_delay, st.session_state.sc_trucks, st.session_state.sc_sl
base_plan = current_plan()
scen_plan = current_plan(uplift=up if aware else 0.0, extra_delay=dl, service_level=sl, trucks=tk)

with st.spinner("Simulating 28 days…"):
    key = (ds["source"], len(ds["forecast"]), float(ds["stock"]["current_stock_kL"].sum()))
    base_k, base_trips = scenario_sim(key, ds["outlets"], ds["stock"], ds["forecast"], ds["models"], ds["as_of"],
                                      0.0, 0, cfg["trucks_per_day"], cfg["service_level"], True)
    sc_k, sc_trips = scenario_sim(key, ds["outlets"], ds["stock"], ds["forecast"], ds["models"], ds["as_of"],
                                  up, dl, tk, sl, aware)


def today(p):
    o = p[p["decision"] != "No order"]
    return dict(red=int((p["status"] == "Red").sum()), orders=len(o), trips=int(o["trips"].sum()),
                deferred=int((p["decision"] == "Deferred (truck limit)").sum()))


b, s = today(base_plan), today(scen_plan)
st.subheader("Base vs scenario")
rows = [
    ("Tomorrow: outlets in Red", b["red"], s["red"], True),
    ("Tomorrow: truck trips needed", b["trips"], s["trips"], True),
    ("Tomorrow: orders without a truck", b["deferred"], s["deferred"], True),
    ("28 days: dry-out outlet-days (avg)", base_k["dry_out_outlet_days"], sc_k["dry_out_outlet_days"], True),
    ("28 days: lost sales (kL)", base_k["lost_kL"], sc_k["lost_kL"], True),
    ("28 days: avg truck trips per day", base_k["trips_per_day"], sc_k["trips_per_day"], True),
    ("28 days: days at the truck limit", base_k["days_at_truck_limit"], sc_k["days_at_truck_limit"], True),
]
cols = st.columns(4)
for i, (label, bv, sv, bad_up) in enumerate(rows):
    cols[i % 4].metric(label, f"{sv:,.1f}" if isinstance(sv, float) else f"{sv:,}",
                       delta=f"{sv - bv:+,.1f} vs base" if isinstance(sv, float) else f"{sv - bv:+,} vs base",
                       delta_color="inverse" if bad_up else "normal")

g = go.Figure()
x = pd.date_range(pd.Timestamp(ds["as_of"]) + pd.Timedelta(days=1), periods=len(base_trips))
g.add_trace(go.Scatter(x=x, y=base_trips, name="Base: trips used", line=dict(color="#5b6b7b")))
g.add_trace(go.Scatter(x=x, y=sc_trips, name="Scenario: trips used", line=dict(color="#d9822b", width=3)))
g.add_hline(y=tk, line=dict(color="#d64545", dash="dash"), annotation_text=f"Scenario truck limit ({tk})")
g.update_layout(height=320, margin=dict(t=20, b=10), yaxis_title="Truck trips per day", legend=dict(orientation="h", y=-0.2))
st.plotly_chart(g, width="stretch")

st.subheader("What should the manager do?")
msgs = []
if sc_k["days_at_truck_limit"] >= 3:
    extra = max(1, int(round(max(sc_trips) - tk + 0.5)) + 2)
    msgs.append(f"🚚 Trucks are the bottleneck on {sc_k['days_at_truck_limit']:.0f} of 28 days. Arrange about **{extra} extra trips/day** "
                "on standby with transporters, or pre-position stock at highway/rural outlets before the event.")
if sc_k["dry_out_outlet_days"] > base_k["dry_out_outlet_days"] * 1.5 + 2:
    msgs.append("🔴 Dry-outs rise sharply. Raise the service level for highway and rural outlets and dispatch earlier "
                "(the Planner already prioritises lowest days of cover).")
if up > 0 and not aware:
    msgs.append("📈 The surge hurts more when it is a surprise — switch the toggle on to see the benefit of updating the "
                "forecast as soon as the price gap or festival is known.")
if dl > 0:
    msgs.append(f"⏱️ A {dl}-day delay lengthens the protection period, so reorder points rise and more outlets turn Amber/Red now. "
                "Order today for every Amber outlet rather than waiting.")
if not msgs:
    msgs.append("✅ The plan absorbs this scenario: dry-out risk and truck usage stay close to the base case.")
for m in msgs:
    st.markdown(m)

with st.expander("Scenario dispatch list for tomorrow"):
    st.dataframe(scen_plan[scen_plan["decision"] != "No order"][["priority", "outlet_id", "product", "status", "days_of_cover",
                                                               "reorder_point_kL", "order_kL", "decision"]],
                 hide_index=True, width="stretch")
