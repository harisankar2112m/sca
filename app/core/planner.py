"""Replenishment decision logic (uses the JMP demand forecasts).

Timing convention (same as the data generator):
  decision at the end of day 0  ->  truck leaves the depot on day 1
  ->  fuel arrives at the START of day `transit_days` (before that day's sales).
So if we order today, the outlet must survive Lx = transit - 1 (+ delay) days of sales.
If we do NOT order today, the next chance is tomorrow, so the protection period is
P = Lx + 1 review day = transit (+ delay) days.

  safety stock  SS  = z * sigma_P                 (sigma_P from the JMP 95% intervals)
  reorder point ROP = dead stock + forecast demand over P days + SS
  order when stock <= ROP; quantity fills the tank's expected free space on arrival,
  rounded DOWN to whole 4 kL compartments (never overfills)
  trucks: one 20 kL trip carries up to 5 compartments; the depot has K trips per day.
  If more trips are needed than K, outlets are served in order of days of cover.
"""
import math

import numpy as np
import pandas as pd
from scipy.stats import norm

COMPARTMENT_KL = 4.0
TRUCK_KL = 20.0
Z95 = 1.959964
REACTIVE_TRIGGER = {"Urban": 0.35, "Highway": 0.50, "Rural": 0.55}   # current dealer practice


def days_of_cover(usable: float, daily: np.ndarray) -> float:
    """Days until usable stock is used up by the forecast (fractional; capped at horizon)."""
    if usable <= 0:
        return 0.0
    cum = np.cumsum(daily)
    k = int(np.searchsorted(cum, usable))
    if k >= len(daily):
        return float(len(daily))
    prev = cum[k - 1] if k else 0.0
    return k + (usable - prev) / max(daily[k], 1e-9)


def plan(outlets: pd.DataFrame, stock: pd.DataFrame, fc: pd.DataFrame, as_of,
         service_level=0.98, trucks_per_day=34, demand_uplift=0.0, extra_delay=0) -> pd.DataFrame:
    """One-day dispatch plan. stock: outlet_id, product, current_stock_kL. fc: daily forecasts after as_of."""
    z = norm.ppf(service_level)
    o = outlets.set_index("outlet_id")
    st = stock.set_index(["outlet_id", "product"])["current_stock_kL"]
    fc = fc[fc["date"] > pd.Timestamp(as_of)].sort_values("date")
    rows = []
    for (oid, prod), g in fc.groupby(["outlet_id", "product"]):
        if oid not in o.index or (oid, prod) not in st.index:
            continue
        d = g["forecast"].to_numpy() * (1 + demand_uplift)
        sd = (g["hi95"] - g["lo95"]).to_numpy() / (2 * Z95) * (1 + demand_uplift)
        r = o.loc[oid]
        cap, dead = r[f"{prod.lower()}_capacity_kL"], r[f"{prod.lower()}_dead_stock_kL"]
        s = float(st[(oid, prod)])
        lx = int(r["transit_days"]) - 1 + int(extra_delay)
        p = lx + 1
        usable = s - dead
        mu_p, sig_p = d[:p].sum(), math.sqrt((sd[:p] ** 2).sum())
        ss = z * sig_p
        rop = dead + mu_p + ss
        cover = days_of_cover(usable, d)
        p_dry = float(1 - norm.cdf((usable - mu_p) / sig_p)) if sig_p > 0 else float(usable < mu_p)
        need = s <= rop
        q = 0.0
        if need:
            space_on_arrival = cap - max(s - d[:lx].sum(), dead)
            q = math.floor(space_on_arrival / COMPARTMENT_KL) * COMPARTMENT_KL
            q = max(q, 0.0)
        status = "Red" if cover < p else ("Amber" if need else "Green")
        rows.append(dict(
            outlet_id=oid, outlet_type=r["outlet_type"], product=prod, current_stock_kL=round(s, 1),
            capacity_kL=cap, dead_stock_kL=dead, fill_pct=round(100 * s / cap, 0),
            avg_daily_forecast_kL=round(float(d[:7].mean()), 2), days_of_cover=round(cover, 1),
            transit_days=int(r["transit_days"]), protection_days=p,
            safety_stock_kL=round(ss, 1), reorder_point_kL=round(rop, 1),
            dryout_prob_if_no_order=round(p_dry, 3), status=status,
            order_kL=q, trips=int(math.ceil(q / TRUCK_KL)) if q > 0 else 0,
            expected_dryout_date=(pd.Timestamp(as_of) + pd.Timedelta(days=math.ceil(cover))).date()
            if cover < len(d) else None,
        ))
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # priority under the truck limit: lowest days of cover first, then highest dry-out risk
    df = df.sort_values(["days_of_cover", "dryout_prob_if_no_order"], ascending=[True, False]).reset_index(drop=True)
    used, decision, prio = 0, [], []
    k = 0
    for r in df.itertuples():
        if r.order_kL <= 0:
            decision.append("No order"); prio.append(None); continue
        k += 1
        prio.append(k)
        if used + r.trips <= trucks_per_day:
            used += r.trips; decision.append("Dispatch today")
        else:
            decision.append("Deferred (truck limit)")
    df["priority"] = prio
    df["decision"] = decision
    dispatch = pd.Timestamp(as_of) + pd.Timedelta(days=1)
    df["dispatch_date"] = np.where(df["decision"] == "Dispatch today", dispatch.date(), None)
    df["arrival_date"] = [
        (dispatch + pd.Timedelta(days=int(t) - 1 + int(extra_delay))).date() if dec == "Dispatch today" else None
        for t, dec in zip(df["transit_days"], df["decision"])]
    df["recommendation"] = df.apply(_recommend, axis=1)
    return df


def _recommend(r) -> str:
    who = f"{r['outlet_id']} {r['product']}"
    cover, dec = r["days_of_cover"], r["decision"]
    if dec == "Dispatch today":
        loads = int(r["order_kL"] // COMPARTMENT_KL)
        return (f"Dispatch {r['order_kL']:.0f} kL ({loads} compartments) to {who} tomorrow - "
                f"stock covers {cover:.1f} days, delivery takes {r['transit_days']} day(s).")
    if dec == "Deferred (truck limit)":
        return (f"NO TRUCK for {who}: {cover:.1f} days of cover. Hire an extra truck or "
                f"ration sales; dry-out risk {100 * r['dryout_prob_if_no_order']:.0f}%.")
    if r["status"] == "Red":
        return f"{who} is low but the tank cannot take a full compartment yet - recheck the dip tomorrow."
    return f"{who} OK - {cover:.1f} days of cover."


# --------------------------------------------------------------------------- simulation
def simulate(outlets, keys, demand, fc_mean, fc_sd, start_stock, policy="forecast",
             service_level=0.98, trucks_per_day=34, extra_delay=0, delay_prob=0.08, seed=7):
    """Day-by-day simulation of a replenishment policy against a demand path.

    keys: list of (outlet_id, product); demand: (n_keys, n_days) actual demand;
    fc_mean/fc_sd: (n_keys, n_days + pad) forecast mean/sd for each future day (used by 'forecast');
    policy 'reactive' = current dealer rule (indent below a fixed % of tank, FIFO trucks).
    Returns daily results and summary KPIs.
    """
    rng = np.random.default_rng(seed)
    z = norm.ppf(service_level)
    o = outlets.set_index("outlet_id")
    nk, n = demand.shape
    cap = np.array([o.at[k, f"{p.lower()}_capacity_kL"] for k, p in keys], float)
    dead = np.array([o.at[k, f"{p.lower()}_dead_stock_kL"] for k, p in keys], float)
    transit = np.array([int(o.at[k, "transit_days"]) for k, _ in keys])
    otype = [o.at[k, "outlet_type"] for k, _ in keys]
    stock = np.minimum(np.array(start_stock, float), cap)
    pending = np.zeros(nk, bool)
    arrivals = {}
    queue = []
    lost = np.zeros((nk, n)); dry = np.zeros((nk, n), bool); trips_day = np.zeros(n, int)
    for t in range(n):
        for i, q in arrivals.pop(t, []):
            stock[i] += min(q, cap[i] - stock[i]); pending[i] = False
        avail = np.maximum(stock - dead, 0)
        sold = np.minimum(demand[:, t], avail)
        lost[:, t] = demand[:, t] - sold
        dry[:, t] = lost[:, t] > 0.05
        stock -= sold
        # ---- orders at end of day t
        if policy == "reactive":
            for i in range(nk):
                if not pending[i] and stock[i] < REACTIVE_TRIGGER[otype[i]] * cap[i]:
                    q = math.floor((cap[i] - stock[i]) / COMPARTMENT_KL) * COMPARTMENT_KL
                    if q >= COMPARTMENT_KL:
                        queue.append((i, q)); pending[i] = True
            cands = queue
        else:
            cands, cover = [], []
            for i in range(nk):
                if pending[i]:
                    continue
                lx = transit[i] - 1 + extra_delay
                p = lx + 1
                mu = fc_mean[i, t + 1:t + 1 + p]
                sg = math.sqrt((fc_sd[i, t + 1:t + 1 + p] ** 2).sum())
                if stock[i] <= dead[i] + mu.sum() + z * sg:
                    q = math.floor((cap[i] - max(stock[i] - fc_mean[i, t + 1:t + 1 + lx].sum(), dead[i]))
                                   / COMPARTMENT_KL) * COMPARTMENT_KL
                    if q >= COMPARTMENT_KL:
                        cands.append((i, q))
                        cover.append(days_of_cover(stock[i] - dead[i], fc_mean[i, t + 1:t + 15]))
            cands = [c for _, c in sorted(zip(cover, cands), key=lambda x: x[0])]
        left, waiting = trucks_per_day, []
        for i, q in cands:
            tr = math.ceil(q / TRUCK_KL)
            if tr <= left:
                left -= tr
                arr = t + transit[i] + extra_delay + int(rng.random() < delay_prob)
                arrivals.setdefault(arr, []).append((i, q)); pending[i] = True
            else:
                waiting.append((i, q))
        trips_day[t] = trucks_per_day - left
        queue = waiting if policy == "reactive" else []
    total = demand.sum()
    return dict(
        dry=dry, lost=lost, trips=trips_day,
        kpi=dict(dry_out_outlet_days=int(dry.sum()), dry_out_rate_pct=round(100 * dry.mean(), 2),
                 lost_kL=round(float(lost.sum()), 1), lost_pct=round(100 * float(lost.sum()) / total, 2),
                 trips=int(trips_day.sum()), trips_per_day=round(float(trips_day.mean()), 1),
                 peak_trips=int(trips_day.max()), days_at_truck_limit=int((trips_day >= trucks_per_day).sum())))


def forecast_arrays(fc: pd.DataFrame, keys, start, n_days, models: pd.DataFrame | None = None,
                    pad: int = 15, uplift: float = 0.0):
    """Mean/sd arrays (n_keys, n_days+pad) from a forecast table starting at `start`.
    Days beyond the forecast horizon repeat the last 7 days (weekly pattern).
    sd uses the model's one-step sigma (relative for multiplicative-error models) if given,
    otherwise the width of the first-day 95% interval."""
    total = n_days + pad
    mean = np.zeros((len(keys), total)); sd = np.zeros_like(mean)
    sig = {} if models is None else dict(zip(models["series"], zip(models["model"], models["sigma"])))
    for i, (oid, prod) in enumerate(keys):
        g = fc[(fc.outlet_id == oid) & (fc["product"] == prod) & (fc.date >= start)].sort_values("date")
        m = g["forecast"].to_numpy()
        if len(m) < total:
            reps = int(np.ceil((total - len(m)) / 7))
            m = np.r_[m, np.tile(m[-7:], reps)]
        m = m[:total] * (1 + uplift)
        mean[i] = m
        name, s = sig.get(f"{oid} {prod}", (None, None))
        if s is not None:
            sd[i] = m * s if str(name).startswith("M") else s
        else:
            first = (g["hi95"].iloc[0] - g["lo95"].iloc[0]) / (2 * Z95)
            sd[i] = m * first / max(g["forecast"].iloc[0], 1e-9)
    return mean, sd
