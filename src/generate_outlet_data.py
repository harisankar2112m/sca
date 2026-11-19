"""Synthetic outlet-level data for DryOut Shield (disclosed as SYNTHETIC).

Why synthetic: OMCs do not publish outlet-level daily sales, stock, tank
sizes or depot lead times. This script builds a realistic depot network of
30 outlets whose demand is anchored to REAL market data:

    demand[i,p,t] = base[i,p]                      outlet size (by outlet type)
                  x market[p,t]                    PPAC monthly per-day consumption,
                                                   indexed to FY2023-24 = 1 (trend + seasonality)
                  x weekday[type,p,dow]            weekly pattern
                  x event[i,p,t]                   festivals, harvest, strike panic, 2026 diesel shift
                  x drift[i]^years                 outlet-specific growth vs market
                  x exp(noise)                     AR(1) log-noise

It then simulates the CURRENT (reactive) replenishment practice so that the
data also contains stock, deliveries and dry-outs:

  * dealer raises an indent when closing stock < trigger share of tank capacity
    and asks to fill the tank, in 4 kL compartment multiples;
  * the depot has K tank-truck trips per day (20 kL each) and dispatches
    indents first-come-first-served;
  * transit time depends on outlet type, with random delays; no dispatch
    during the Jan 2024 truckers' strike;
  * sales = min(demand, stock above dead stock); the rest is lost (dry-out).

Recorded sales are therefore CENSORED on dry-out days, exactly like real
outlet data. True demand is also saved (only possible because it is synthetic).

Run:  python src/generate_outlet_data.py      (seed fixed -> reproducible)
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 2026
START, END = "2023-04-01", "2026-10-31"
DATA = Path(__file__).resolve().parents[1] / "data"
PRODUCTS = ["MS", "HSD"]

COMPARTMENT_KL = 4.0      # tank-truck compartment size
TRUCK_KL = 20.0           # one trip carries up to 20 kL (5 compartments)
TRUCKS_PER_DAY = 34       # depot's daily trip capacity K (baseline)

# ---------------------------------------------------------------- outlet types
# base daily demand (kL/day, FY2023-24 level), tank capacity (kL), transit days
TYPES = {
    "Urban":   dict(n=12, ms=(4, 8), hsd=(4, 8), ms_cap=(20, 30), hsd_cap=(30, 40),
                    km=(5, 40), transit=1, noise=0.07, trigger=0.35),
    "Highway": dict(n=10, ms=(2, 4), hsd=(8, 14), ms_cap=(15, 20), hsd_cap=(40, 60),
                    km=(60, 180), transit=1, noise=0.10, trigger=0.50),
    "Rural":   dict(n=8, ms=(1, 2.5), hsd=(2.5, 5), ms_cap=(10, 15), hsd_cap=(20, 25),
                    km=(80, 220), transit=2, noise=0.13, trigger=0.55),
}
# weekday multipliers Mon..Sun
WEEKDAY = {
    ("Urban", "MS"):    [1.00, 0.98, 0.98, 1.00, 1.05, 1.06, 0.93],
    ("Urban", "HSD"):   [1.03, 1.02, 1.02, 1.02, 1.02, 0.98, 0.91],
    ("Highway", "MS"):  [0.97, 0.96, 0.96, 0.98, 1.03, 1.06, 1.04],
    ("Highway", "HSD"): [1.03, 1.03, 1.03, 1.02, 1.00, 0.97, 0.92],
    ("Rural", "MS"):    [1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00],   # market day added per outlet
    ("Rural", "HSD"):   [1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00],
}

# ---------------------------------------------------------------- events
# (name, start, end, applies_to, product, effect)  effect = demand multiplier
DIWALI = ["2023-11-12", "2024-10-31", "2025-10-20"]
DUSSEHRA = ["2023-10-24", "2024-10-12", "2025-10-02", "2026-10-20"]
HOLI = ["2024-03-25", "2025-03-14", "2026-03-04"]
STRIKE = ("2024-01-01", "2024-01-03")                 # truckers' hit-and-run law protest
DIESEL_SHIFT = ("2026-04-20", "2026-06-30")            # bulk-to-retail diesel shift (stylised)
HARVEST = [("10-15", "11-30"), ("03-25", "04-30")]     # kharif and rabi harvest windows


def build_events(dates: pd.DatetimeIndex) -> pd.DataFrame:
    rows = []

    def add(name, d0, d1, types, prods, mult, note):
        rows.append(dict(event=name, start=pd.Timestamp(d0), end=pd.Timestamp(d1),
                         outlet_types=",".join(types), products=",".join(prods),
                         demand_multiplier=mult, note=note))
    allt = list(TYPES)
    for d in DIWALI:
        d = pd.Timestamp(d)
        add("Diwali run-up", d - pd.Timedelta(days=5), d - pd.Timedelta(days=1), allt, ["MS"], 1.12,
            "festive travel and shopping")
        add("Diwali day", d, d, allt, PRODUCTS, 0.75, "shops and transport shut")
        add("Post-Diwali lull", d + pd.Timedelta(days=1), d + pd.Timedelta(days=3), allt, ["HSD"], 0.85,
            "truck drivers on leave")
    for d in DUSSEHRA:
        d = pd.Timestamp(d)
        add("Dussehra", d - pd.Timedelta(days=2), d, allt, ["MS"], 1.08, "festive travel")
    for d in HOLI:
        add("Holi", d, d, allt, PRODUCTS, 0.65, "holiday")
    add("Truckers' strike - panic buying", STRIKE[0], STRIKE[1], allt, ["MS"], 1.35,
        "Jan 2024 protest; queues at pumps; no tank-truck dispatch")
    add("Truckers' strike - panic buying", STRIKE[0], STRIKE[1], allt, ["HSD"], 1.20,
        "Jan 2024 protest; no tank-truck dispatch")
    add("Bulk-to-retail diesel shift", DIESEL_SHIFT[0], DIESEL_SHIFT[1], ["Highway", "Rural"], ["HSD"], 1.30,
        "price gap pushes bulk buyers to retail pumps (stylised from May 2026 news)")
    for y in range(dates[0].year, dates[-1].year + 1):
        for a, b in HARVEST:
            add("Harvest season", f"{y}-{a}", f"{y}-{b}", ["Rural"], ["HSD"], 1.20,
                "tractors and harvesters")
    ev = pd.DataFrame(rows)
    ev = ev[(ev.end >= dates[0]) & (ev.start <= dates[-1])].reset_index(drop=True)
    return ev


def market_index(dates: pd.DatetimeIndex) -> dict:
    """Daily market factor per product from PPAC per-day consumption, FY2023-24 mean = 1,
    linearly interpolated between mid-month points."""
    ppac = pd.read_csv(DATA / "ppac_monthly_ms_hsd.csv")
    out = {}
    for p in PRODUCTS:
        s = ppac[ppac["product"] == p].copy()
        s["mid"] = pd.to_datetime(s["month"] + "-15")
        base = s.loc[s["financial_year"] == "2023-2024", "per_day_tmt"].mean()
        idx = (s["per_day_tmt"] / base).to_numpy()
        x = (s["mid"] - dates[0]).dt.days.to_numpy()
        out[p] = np.interp((dates - dates[0]).days.to_numpy(), x, idx)
    return out


def make_outlets(rng) -> pd.DataFrame:
    rows = []
    for t, c in TYPES.items():
        for k in range(1, c["n"] + 1):
            km = rng.uniform(*c["km"])
            transit = c["transit"] + (1 if t == "Highway" and km > 130 else 0)
            rows.append(dict(
                outlet_id=f"{t[0]}-{k:02d}", outlet_type=t,
                distance_km=round(km),
                transit_days=transit,
                ms_capacity_kL=float(rng.choice(np.arange(c["ms_cap"][0], c["ms_cap"][1] + 1, 5))),
                hsd_capacity_kL=float(rng.choice(np.arange(c["hsd_cap"][0], c["hsd_cap"][1] + 1, 5))),
                ms_base_kL=round(rng.uniform(*c["ms"]), 2),
                hsd_base_kL=round(rng.uniform(*c["hsd"]), 2),
                growth_vs_market=round(rng.normal(0, 0.03), 3),
                market_day=int(rng.integers(0, 7)) if t == "Rural" else -1,
            ))
    o = pd.DataFrame(rows)
    o["ms_dead_stock_kL"] = (0.05 * o["ms_capacity_kL"]).round(1)
    o["hsd_dead_stock_kL"] = (0.05 * o["hsd_capacity_kL"]).round(1)
    return o


def true_demand(o: pd.DataFrame, dates, events, rng) -> dict:
    mkt = market_index(dates)
    years = (dates - dates[0]).days.to_numpy() / 365.25
    dow = dates.day_of_week.to_numpy()
    dem = {}
    for _, r in o.iterrows():
        for p in PRODUCTS:
            base = r[f"{p.lower()}_base_kL"]
            wk = np.array(WEEKDAY[(r.outlet_type, p)])[dow]
            if r.market_day >= 0:
                wk = wk * np.where(dow == r.market_day, 1.18, 0.97)
            ev = np.ones(len(dates))
            for _, e in events.iterrows():
                if r.outlet_type in e.outlet_types.split(",") and p in e.products.split(","):
                    m = (dates >= e.start) & (dates <= e.end)
                    if e.event == "Bulk-to-retail diesel shift":
                        # ramps up, peaks mid-window, tapers off
                        k = np.linspace(0, np.pi, m.sum())
                        ev[m] *= 1 + (e.demand_multiplier - 1) * np.sin(k) * rng.uniform(0.8, 1.2)
                    else:
                        ev[m] *= e.demand_multiplier
            sd = TYPES[r.outlet_type]["noise"]
            eps = rng.normal(0, sd * np.sqrt(1 - 0.3 ** 2), len(dates))
            z = np.zeros(len(dates))
            for t in range(len(dates)):
                z[t] = 0.3 * (z[t - 1] if t else 0) + eps[t]
            d = base * mkt[p] * wk * ev * (1 + r.growth_vs_market) ** years * np.exp(z - sd ** 2 / 2)
            dem[(r.outlet_id, p)] = np.round(np.clip(d, 0, None), 2)
    return dem


def simulate(o, dates, dem, rng):
    """Reactive (as-is) replenishment: dealer indents at a fixed trigger, depot FIFO, K trips/day."""
    strike = set(pd.date_range(*STRIKE))
    keys = list(dem)
    cap = {(r.outlet_id, p): r[f"{p.lower()}_capacity_kL"] for _, r in o.iterrows() for p in PRODUCTS}
    dead = {(r.outlet_id, p): r[f"{p.lower()}_dead_stock_kL"] for _, r in o.iterrows() for p in PRODUCTS}
    info = o.set_index("outlet_id")
    stock = {k: round(0.7 * cap[k], 2) for k in keys}
    pending = {k: False for k in keys}
    queue = []                 # indents waiting for a truck: dict(outlet, product, qty, indent_date)
    arrivals = {}              # date -> list of (key, qty)
    recs, dels = [], []
    for t, day in enumerate(dates):
        # 1) receipts arrive at the start of the day
        rec_today = {k: 0.0 for k in keys}
        for k, q, di in arrivals.pop(day, []):
            q = min(q, cap[k] - stock[k])          # cannot overfill the tank (excess is short-delivered)
            stock[k] += q
            rec_today[k] += q
            pending[k] = False
            dels[di]["received_kL"] = round(q, 2)
        # 2) sales
        for k in keys:
            opening = stock[k]
            avail = max(opening - dead[k], 0.0)
            d = dem[k][t]
            s = min(d, avail)
            stock[k] = opening - s
            recs.append((day, k[0], k[1], round(opening - rec_today[k], 2), round(rec_today[k], 2),
                         round(s, 2), round(stock[k], 2), d, round(d - s, 2), int(d - s > 0.05)))
        # 3) dealer indents (end of day)
        for k in keys:
            if not pending[k] and stock[k] < TYPES[info.at[k[0], "outlet_type"]]["trigger"] * cap[k]:
                q = np.floor((cap[k] - stock[k]) / COMPARTMENT_KL) * COMPARTMENT_KL
                if q >= COMPARTMENT_KL:
                    queue.append(dict(outlet_id=k[0], product=k[1], qty=q, indent_date=day))
                    pending[k] = True
        # 4) depot dispatches next morning's trips FIFO (no dispatch during strike)
        nxt = day + pd.Timedelta(days=1)
        if nxt in strike:
            continue
        trips_left = TRUCKS_PER_DAY
        waiting = []
        for ind in queue:
            trips = int(np.ceil(ind["qty"] / TRUCK_KL))
            if trips <= trips_left:
                trips_left -= trips
                transit = int(info.at[ind["outlet_id"], "transit_days"])
                delay = int(rng.random() < 0.08)              # random 1-day delay (breakdown, depot queue)
                arr = nxt + pd.Timedelta(days=transit - 1 + delay)
                arr = max(arr, nxt)
                dels.append(dict(indent_date=ind["indent_date"], outlet_id=ind["outlet_id"],
                                 product=ind["product"], indent_kL=ind["qty"], dispatch_date=nxt,
                                 arrival_date=arr, trips=trips, received_kL=np.nan))
                arrivals.setdefault(arr, []).append(((ind["outlet_id"], ind["product"]), ind["qty"],
                                                     len(dels) - 1))
            else:
                waiting.append(ind)
        queue = waiting
    daily = pd.DataFrame(recs, columns=["date", "outlet_id", "product", "opening_stock_kL", "receipt_kL",
                                        "sales_kL", "closing_stock_kL", "true_demand_kL",
                                        "lost_sales_kL", "dry_out"])
    deliveries = pd.DataFrame(dels)
    deliveries["lead_time_days"] = (deliveries["arrival_date"] - deliveries["indent_date"]).dt.days
    return daily, deliveries


def main():
    rng = np.random.default_rng(SEED)
    dates = pd.date_range(START, END, freq="D")
    outlets = make_outlets(rng)
    events = build_events(dates)
    dem = true_demand(outlets, dates, events, rng)
    daily, deliveries = simulate(outlets, dates, dem, rng)

    DATA.mkdir(exist_ok=True)
    # outlet master (what a depot would know) and hidden generator parameters (ground truth)
    master_cols = ["outlet_id", "outlet_type", "distance_km", "transit_days", "ms_capacity_kL",
                   "hsd_capacity_kL", "ms_dead_stock_kL", "hsd_dead_stock_kL"]
    outlets[master_cols].to_csv(DATA / "outlets.csv", index=False)
    outlets.to_csv(DATA / "synthetic_generator_parameters.csv", index=False)
    daily.to_csv(DATA / "outlet_daily_sales.csv", index=False, date_format="%Y-%m-%d")
    deliveries.to_csv(DATA / "deliveries_asis.csv", index=False, date_format="%Y-%m-%d")
    ev = events.copy()
    ev["start"] = ev["start"].dt.strftime("%Y-%m-%d")
    ev["end"] = ev["end"].dt.strftime("%Y-%m-%d")
    ev.to_csv(DATA / "events_calendar.csv", index=False)

    print(f"{len(outlets)} outlets x {len(PRODUCTS)} products x {len(dates)} days = {len(daily):,} rows")
    print(daily.assign(year=daily.date.dt.year)
          .merge(outlets[["outlet_id", "outlet_type"]], on="outlet_id")
          .groupby(["year", "outlet_type"])
          .agg(dry_out_days=("dry_out", "sum"), lost_kL=("lost_sales_kL", "sum"),
               sales_kL=("sales_kL", "sum")).round(0))


if __name__ == "__main__":
    main()
