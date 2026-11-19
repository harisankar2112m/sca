"""Loading the built-in sample data and holding the active dataset in session state."""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from core.planner import forecast_arrays, plan, simulate

APP = Path(__file__).resolve().parents[1]
DATA = APP / "data"
ASSETS = APP / "assets"

DEFAULTS = dict(service_level=0.98, trucks_per_day=34)


@st.cache_data(show_spinner=False)
def load_sample():
    outlets = pd.read_csv(DATA / "outlets.csv")
    sales = pd.read_csv(DATA / "outlet_daily_sales.csv", parse_dates=["date"])
    fc = pd.read_csv(DATA / "forecast_next28.csv", parse_dates=["date"])
    models = pd.read_csv(DATA / "jmp_models.csv")
    as_of = sales["date"].max()
    stock = sales[sales["date"] == as_of][["outlet_id", "product", "closing_stock_kL"]] \
        .rename(columns={"closing_stock_kL": "current_stock_kL"}).assign(as_of_date=as_of)
    return dict(source="Built-in sample (synthetic outlets calibrated to PPAC; forecasts from JMP)",
                forecast_engine="JMP Time Series Forecast", outlets=outlets, sales=sales,
                forecast=fc, models=models, stock=stock.reset_index(drop=True), as_of=as_of)


@st.cache_data(show_spinner=False)
def load_ppac():
    return pd.read_csv(DATA / "ppac_monthly_ms_hsd.csv")


@st.cache_data(show_spinner=False)
def load_validation():
    v = pd.read_csv(DATA / "jmp_validation_forecasts.csv", parse_dates=["date"])
    v["series"] = v["by_group"].str.replace("series=", "", regex=False).str.strip()
    v[["outlet_id", "product"]] = v["series"].str.split(" ", expand=True)
    v = v.rename(columns={"demand_kL": "forecast", "demand_kL (Lower 95%)": "lo95", "demand_kL (Upper 95%)": "hi95"})
    comp = pd.read_csv(DATA / "model_comparison.csv")
    per = pd.read_csv(DATA / "holdout_by_series.csv")
    return v.drop(columns="by_group"), comp, per


def get_ds() -> dict:
    if "ds" not in st.session_state:
        st.session_state.ds = load_sample()
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, v)
    return st.session_state.ds


def settings() -> dict:
    get_ds()
    return {k: st.session_state[k] for k in DEFAULTS}


def current_plan(uplift=0.0, extra_delay=0, service_level=None, trucks=None) -> pd.DataFrame:
    ds, s = get_ds(), settings()
    return _plan_cached(ds["source"], len(ds["forecast"]), ds["outlets"], ds["stock"], ds["forecast"], ds["as_of"],
                        service_level or s["service_level"], trucks or s["trucks_per_day"], uplift, extra_delay)


@st.cache_data(show_spinner=False)
def _plan_cached(_src, _n, outlets, stock, fc, as_of, sl, k, uplift, delay):
    return plan(outlets, stock, fc, as_of, sl, k, uplift, delay)


@st.cache_data(show_spinner=False)
def backtest(service_level: float, trucks: int, extra_delay: int = 0, seed: int = 7):
    """Replay the 56-day JMP holdout (6 Sep - 31 Oct 2026) with true demand:
    current reactive practice vs the forecast-driven policy, same trucks and random delays."""
    ds = load_sample()
    v, _, _ = load_validation()
    s = ds["sales"]
    start = v["date"].min()
    hold = s[s["date"] >= start].sort_values("date")
    keys = sorted(set(zip(hold["outlet_id"], hold["product"])))
    g = {k: d for k, d in hold.groupby(["outlet_id", "product"])}
    demand = np.array([g[k]["true_demand_kL"].to_numpy() for k in keys])
    first = hold[hold["date"] == start].set_index(["outlet_id", "product"])
    st0 = [first.at[k, "opening_stock_kL"] + first.at[k, "receipt_kL"] for k in keys]
    mean, sd = forecast_arrays(v, keys, start, demand.shape[1], ds["models"])
    out = {}
    for pol in ("reactive", "forecast"):
        r = simulate(ds["outlets"], keys, demand, mean, sd, st0, policy=pol, service_level=service_level,
                     trucks_per_day=trucks, extra_delay=extra_delay, seed=seed)
        out[pol] = r
    dates = pd.date_range(start, periods=demand.shape[1])
    return out, dates, keys


@st.cache_data(show_spinner=False)
def scenario_sim(_key, outlets, stock, fc, models, as_of, uplift, extra_delay, trucks, service_level,
                 planner_aware, n_days=28, reps=10):
    """Forward simulation of the next n_days under a scenario, averaged over `reps` random demand paths.
    Demand = forecast x (1 + uplift) x noise. If planner_aware, the planner's forecast includes the uplift."""
    keys = sorted(set(zip(stock["outlet_id"], stock["product"])) & set(zip(fc["outlet_id"], fc["product"])))
    start = pd.Timestamp(as_of) + pd.Timedelta(days=1)
    mean, sd = forecast_arrays(fc, keys, start, n_days, models)
    st_ = stock.set_index(["outlet_id", "product"])["current_stock_kL"]
    st0 = [float(st_[k]) for k in keys]
    rng = np.random.default_rng(11)
    agg, trips = [], np.zeros(n_days)
    plan_mean = mean * (1 + uplift) if planner_aware else mean
    for r in range(reps):
        true = np.clip(mean[:, :n_days] * (1 + uplift) + rng.normal(0, 1, (len(keys), n_days)) * sd[:, :n_days], 0, None)
        res = simulate(outlets, keys, true, plan_mean, sd, st0, policy="forecast", service_level=service_level,
                       trucks_per_day=trucks, extra_delay=extra_delay, seed=100 + r)
        agg.append(res["kpi"]); trips += res["trips"] / reps
    k = pd.DataFrame(agg).mean().to_dict()
    return k, trips
