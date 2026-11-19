import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.data import ASSETS, get_ds, load_sample, load_validation

st.title("Demand Forecast")
ds = get_ds()
sales, fc, models = ds["sales"], ds["forecast"], ds["models"]
is_sample = ds["source"].startswith("Built-in")

st.caption(f"Forecast engine: **{ds['forecast_engine']}** · horizon {fc['date'].nunique()} days "
           f"({fc['date'].min():%d %b} – {fc['date'].max():%d %b %Y}) · 95% forecast intervals")

c1, c2, c3 = st.columns([1, 1, 2])
outlets = sorted(fc["outlet_id"].unique())
oid = c1.selectbox("Outlet", outlets, index=outlets.index("H-03") if "H-03" in outlets else 0)
prod = c2.radio("Product", ["HSD", "MS"], horizontal=True, format_func=lambda x: {"MS": "Petrol (MS)", "HSD": "Diesel (HSD)"}[x])
hist_days = c3.slider("History shown (days)", 30, 730, 120, step=30)

h = sales[(sales["outlet_id"] == oid) & (sales["product"] == prod)].sort_values("date").tail(hist_days)
f = fc[(fc["outlet_id"] == oid) & (fc["product"] == prod)].sort_values("date")
if f.empty:
    st.warning("No forecast for this outlet and product.")
    st.stop()
m = models[models["series"] == f"{oid} {prod}"]

fig = go.Figure()
fig.add_trace(go.Scatter(x=h["date"], y=h["sales_kL"], name="Actual sales", mode="lines", line=dict(color="#5b6b7b", width=1.4)))
if "dry_out" in h:
    d = h[h["dry_out"] == 1]
    fig.add_trace(go.Scatter(x=d["date"], y=d["sales_kL"], name="Dry-out day (sales capped)", mode="markers",
                             marker=dict(color="#d64545", size=7, symbol="x")))
fig.add_trace(go.Scatter(x=pd.concat([f["date"], f["date"][::-1]]), y=pd.concat([f["hi95"], f["lo95"][::-1]]),
                         fill="toself", fillcolor="rgba(47,111,223,0.18)", line=dict(width=0), name="95% interval",
                         hoverinfo="skip"))
fig.add_trace(go.Scatter(x=f["date"], y=f["forecast"], name="Forecast", mode="lines", line=dict(color="#2f6fdf", width=2.5)))
fig.update_layout(height=420, margin=dict(t=20, b=10), yaxis_title="kL per day", hovermode="x unified",
                  legend=dict(orientation="h", y=-0.15))
st.plotly_chart(fig, width="stretch")

k = st.columns(4)
k[0].metric("Avg forecast, next 7 days", f"{f['forecast'].head(7).mean():.2f} kL/day")
k[1].metric("Forecast, next 28 days", f"{f['forecast'].sum():.0f} kL")
last28 = h.tail(28)["sales_kL"].mean() if len(h) else float("nan")
k[2].metric("Last 28 days actual (avg)", f"{last28:.2f} kL/day",
            delta=f"{100 * (f['forecast'].head(28).mean() / last28 - 1):+.1f}% forecast vs recent")
if not m.empty:
    k[3].metric("Model selected", m["model"].iloc[0],
                help="ETS notation: Error / Trend / Season. A = additive, M = multiplicative, N = none. "
                     "E.g. MNM = multiplicative error, no trend, multiplicative weekly season.")

with st.expander("Forecast table"):
    st.dataframe(f[["date", "forecast", "lo95", "hi95"]].round(2), hide_index=True, width="stretch")

st.divider()
st.subheader("Model validation")
if not is_sample:
    st.info("Validation results below are for the built-in sample (the model validated in JMP). For uploaded data the "
            "app refits the same ETS family and selects the specification with the lowest AIC, as JMP does.")
v, comp, per = load_validation()
st.markdown("""The forecasting model was built in **JMP** (*Time Series Forecast* platform). For every outlet × product,
JMP fits a recommended set of exponential-smoothing (ETS) models with a 7-day season and keeps the lowest-AIC model.
It was fitted on data up to **5 Sep 2026** and tested on the next **56 days** it had not seen, against two benchmarks.""")
comp = comp.rename(columns={"method": "Method", "MAPE_%": "MAPE %", "RMSE_kL": "RMSE (kL)", "MAE_kL": "MAE (kL)",
                            "Bias_%": "Bias %", "series_won_on_MAPE": "Series won (of 60)", "coverage_95_%": "95% interval coverage %"})
st.dataframe(comp, hide_index=True, width="stretch")
st.caption("JMP's model has the lowest error, wins 41 of 60 series and its 95% intervals contain 95.3% of actual values, "
           "so the intervals can be trusted for safety stock. All methods under-forecast by about 5% because demand rose "
           "faster than trend in Sep–Oct 2026 (PPAC: diesel +12% year on year in October) — see Scenarios.")

c1, c2 = st.columns([3, 2])
with c1:
    vv = v[(v["outlet_id"] == oid) & (v["product"] == prod)]
    smp = load_sample()["sales"]
    a = smp[(smp["outlet_id"] == oid) & (smp["product"] == prod) & (smp["date"] >= vv["date"].min())] if len(vv) else smp.iloc[:0]
    if len(vv):
        g = go.Figure()
        g.add_trace(go.Scatter(x=pd.concat([vv["date"], vv["date"][::-1]]), y=pd.concat([vv["hi95"], vv["lo95"][::-1]]),
                               fill="toself", fillcolor="rgba(47,111,223,0.15)", line=dict(width=0), name="95% interval"))
        g.add_trace(go.Scatter(x=a["date"], y=a["true_demand_kL"], name="Actual demand", line=dict(color="#5b6b7b")))
        g.add_trace(go.Scatter(x=vv["date"], y=vv["forecast"], name="JMP forecast (made 5 Sep)", line=dict(color="#2f6fdf", width=2.5)))
        g.update_layout(height=320, margin=dict(t=30, b=10), title=f"Holdout check: {oid} {prod}", yaxis_title="kL/day",
                        legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(g, width="stretch")
        r = per[(per["series"] == f"{oid} {prod}") & per["method"].str.startswith("JMP")]
        if len(r):
            st.caption(f"{oid} {prod}: MAPE {r['MAPE_%'].iloc[0]:.1f}%, bias {r['Bias_%'].iloc[0]:+.1f}%, "
                       f"interval coverage {r['coverage_95_%'].iloc[0]:.0f}%")
with c2:
    seg = per[per["method"].str.startswith("JMP")].groupby(["outlet_type", "product"])[["MAPE_%", "coverage_95_%"]].mean().round(1).reset_index()
    seg.columns = ["Outlet type", "Product", "MAPE %", "95% coverage %"]
    st.markdown("**JMP accuracy by segment**")
    st.dataframe(seg, hide_index=True, width="stretch")
    st.caption("Rural diesel is hardest to forecast (harvest spikes, small volumes) → it gets more safety stock automatically.")
    mm = load_sample()["models"]["model"].value_counts().rename_axis("ETS model").reset_index(name="Series")
    st.markdown("**Models selected by JMP**")
    st.dataframe(mm, hide_index=True, width="stretch")

with st.expander("JMP output charts (Time Series Forecast platform)"):
    imgs = sorted(ASSETS.glob("chart_*.png"))
    for p in imgs:
        st.image(str(p), caption=p.stem.replace("chart_", "JMP forecast: ").replace("_", " "))
