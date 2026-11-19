"""Forecasts for UPLOADED data.

The project's model was built and validated in JMP (Time Series Forecast, ETS with
AIC selection, season 7). JMP cannot run inside a web app, so for new data the app
refits the same ETS family in Python (statsmodels ETSModel) and, like JMP, keeps the
lowest-AIC model among the specifications JMP selected for the sample outlets
(ANA, MNA, MNM: error / no trend / season).
"""
import warnings

import numpy as np
import pandas as pd

HISTORY_DAYS = 730
SPECS = {"ANA": ("add", "add"), "MNA": ("mul", "add"), "MNM": ("mul", "mul")}


def correct_dryouts(g: pd.DataFrame, dead_stock: float) -> pd.Series:
    """Same rule as the JMP input: on dry-out days (closing stock at dead stock) replace
    sales by the mean of the same weekday over the previous 4 normal weeks."""
    s = g["sales_kL"].to_numpy(float)
    cs = g["closing_stock_kL"].to_numpy(float)
    dry = np.nan_to_num(cs, nan=np.inf) <= dead_stock + 0.05
    out = s.copy()
    for t in np.where(dry)[0]:
        lags = [t - 7 * k for k in range(1, 9) if t - 7 * k >= 0 and not dry[t - 7 * k]][:4]
        if lags:
            out[t] = max(s[t], s[lags].mean())
    return pd.Series(out, index=g.index)


def fit_one(y: pd.Series, horizon: int = 28) -> dict:
    from statsmodels.tsa.exponential_smoothing.ets import ETSModel
    y = y.asfreq("D").interpolate(limit_direction="both").iloc[-HISTORY_DAYS:]
    best = None
    for name, (err, seas) in SPECS.items():
        if err == "mul" and (y <= 0).any():
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                res = ETSModel(y, error=err, trend=None, seasonal=seas, seasonal_periods=7).fit(disp=False)
            if np.isfinite(res.aic) and (best is None or res.aic < best[1].aic):
                best = (name, res)
        except Exception:  # noqa: BLE001 - a spec that fails is skipped
            continue
    if best is None:
        raise ValueError("no ETS model could be fitted")
    name, res = best
    pred = res.get_prediction(start=len(y), end=len(y) + horizon - 1)
    sf = pred.summary_frame(alpha=0.05)
    idx = pd.date_range(y.index[-1] + pd.Timedelta(days=1), periods=horizon, freq="D")
    sigma = float(np.sqrt(res.mse)) if name == "ANA" else float(np.std(res.resid))
    return dict(model=name, aic=float(res.aic), sigma=sigma,
                fc=pd.DataFrame({"date": idx, "forecast": sf["mean"].to_numpy(),
                                 "lo95": sf["pi_lower"].to_numpy(), "hi95": sf["pi_upper"].to_numpy()}))


def forecast_upload(sales: pd.DataFrame, outlets: pd.DataFrame, horizon: int = 28, progress=None):
    o = outlets.set_index("outlet_id")
    fcs, models = [], []
    groups = list(sales.groupby(["outlet_id", "product"]))
    for i, ((oid, prod), g) in enumerate(groups):
        if progress:
            progress((i + 1) / len(groups), f"Fitting {oid} {prod}")
        g = g.set_index("date").sort_index()
        dead = float(o.at[oid, f"{prod.lower()}_dead_stock_kL"]) if oid in o.index else 0.0
        y = correct_dryouts(g.reset_index(), dead)
        y.index = g.index
        try:
            r = fit_one(y, horizon)
        except ValueError:
            continue
        f = r["fc"].assign(series=f"{oid} {prod}", outlet_id=oid, product=prod, model=r["model"], sigma=r["sigma"])
        fcs.append(f)
        models.append(dict(series=f"{oid} {prod}", model=r["model"], AIC=r["aic"], sigma=r["sigma"]))
    fc = pd.concat(fcs, ignore_index=True)
    fc[["forecast", "lo95", "hi95"]] = fc[["forecast", "lo95", "hi95"]].clip(lower=0)
    return fc, pd.DataFrame(models)
