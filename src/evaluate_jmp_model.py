"""Score the JMP forecasting model on the 56-day holdout and package its outputs.

Inputs  (written by jmp/DryOut_Forecast_Model.jsl):
    jmp/out/validation_forecasts.csv   forecasts for 6 Sep - 31 Oct 2026 from the Train-only fit
    jmp/out/production_forecasts.csv   forecasts for 1-28 Nov 2026 from the all-data fit
    jmp/out/*_models.txt               JMP report text (model type, AIC, parameters) per series
Outputs (model/):
    jmp_models.csv          model chosen by JMP for each series + AIC, sigma, smoothing weights
    holdout_by_series.csv   MAPE / RMSE / bias / 95% coverage per series and method
    model_comparison.csv    overall comparison: JMP ETS vs benchmarks
    forecast_next28.csv     production forecast with 95% limits (used by the app)
"""
from pathlib import Path
import re

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
JOUT = ROOT / "jmp" / "out"
MOUT = ROOT / "model"


def parse_models(path: Path) -> pd.DataFrame:
    rows = []
    for block in path.read_text(encoding="utf-8", errors="ignore").split("\n### ")[1:]:
        series = block.split("\n", 1)[0].replace("series=", "").strip()

        def grab(label, cast=str):
            m = re.search(rf"^\s*{re.escape(label)}\t\s*([^\t\n]+)", block, re.M)
            return cast(m.group(1).strip()) if m else None
        rows.append(dict(
            series=series, model=grab("Model Abbreviation"), error=grab("Error Type"),
            trend=grab("Trend Type"), damped=grab("Damped"), season=grab("Season Type"),
            AIC=grab("AIC", float), BIC=grab("BIC", float), sigma=grab("Sigma", float),
            n_parm=grab("Nparm", int), alpha=grab("alpha", lambda s: float(s.split()[0])),
            beta=grab("beta", lambda s: float(s.split()[0])),
            gamma=grab("gamma", lambda s: float(s.split()[0])),
        ))
    return pd.DataFrame(rows)


def load_fc(path: Path) -> pd.DataFrame:
    f = pd.read_csv(path, parse_dates=["date"])
    f = f.rename(columns={"demand_kL": "forecast", "demand_kL (Lower 95%)": "lo95",
                          "demand_kL (Upper 95%)": "hi95"})
    f["series"] = f["by_group"].str.replace("series=", "", regex=False).str.strip()
    return f.drop(columns="by_group")


def metrics(g: pd.DataFrame, col: str) -> pd.Series:
    e = g[col] - g["demand_kL"]
    return pd.Series({"MAPE_%": 100 * (e.abs() / g["demand_kL"]).mean(),
                      "RMSE_kL": np.sqrt((e ** 2).mean()),
                      "MAE_kL": e.abs().mean(),
                      "Bias_%": 100 * e.sum() / g["demand_kL"].sum()})


def main():
    MOUT.mkdir(exist_ok=True)
    data = pd.read_csv(ROOT / "jmp" / "model_input.csv", parse_dates=["date"])
    train, hold = data[data.split == "Train"], data[data.split == "Holdout"]

    # benchmarks built from the training data only
    last_wk = train[train.date > train.date.max() - pd.Timedelta(days=7)]
    snaive = last_wk.assign(dow=last_wk.date.dt.day_of_week)[["series", "dow", "demand_kL"]] \
        .rename(columns={"demand_kL": "seasonal_naive"})
    ma28 = train[train.date > train.date.max() - pd.Timedelta(days=28)] \
        .groupby("series").demand_kL.mean().rename("moving_avg_28d")

    val = load_fc(JOUT / "validation_forecasts.csv").rename(columns={"forecast": "jmp_ets"})
    h = hold.merge(val, on=["series", "date"], how="left")
    h["dow"] = h.date.dt.day_of_week
    h = h.merge(snaive, on=["series", "dow"]).merge(ma28, on="series")
    assert h["jmp_ets"].notna().all(), "missing JMP forecasts"
    h["in_95"] = (h.demand_kL >= h.lo95) & (h.demand_kL <= h.hi95)

    methods = {"jmp_ets": "JMP Time Series Forecast (ETS, AIC-selected)",
               "seasonal_naive": "Benchmark: seasonal naive (same weekday last week)",
               "moving_avg_28d": "Benchmark: 28-day moving average"}
    per = []
    for col, name in methods.items():
        m = h.groupby(["series", "outlet_type", "product"]).apply(metrics, col=col, include_groups=False)
        per.append(m.assign(method=name).reset_index())
    per = pd.concat(per)
    cov = h.groupby("series").in_95.mean().rename("coverage_95_%") * 100
    per = per.merge(cov, on="series", how="left")
    per.loc[per.method != methods["jmp_ets"], "coverage_95_%"] = np.nan
    per.round(3).to_csv(MOUT / "holdout_by_series.csv", index=False)

    overall = per.groupby("method")[["MAPE_%", "RMSE_kL", "MAE_kL", "Bias_%"]].mean()
    winners = per.pivot_table(index="series", columns="method", values="MAPE_%").idxmin(axis=1)
    overall["series_won_on_MAPE"] = winners.value_counts().reindex(overall.index).fillna(0).astype(int)
    overall["coverage_95_%"] = [h.in_95.mean() * 100 if m == methods["jmp_ets"] else np.nan for m in overall.index]
    overall = overall.sort_values("MAPE_%").round(2)
    overall.to_csv(MOUT / "model_comparison.csv")
    by_type = per[per.method == methods["jmp_ets"]].groupby(["outlet_type", "product"])[["MAPE_%", "RMSE_kL"]] \
        .mean().round(2)

    models = parse_models(JOUT / "production_models.txt")
    models.to_csv(MOUT / "jmp_models.csv", index=False)

    prod = load_fc(JOUT / "production_forecasts.csv")
    prod[["outlet_id", "product"]] = prod["series"].str.split(" ", expand=True)
    prod = prod.merge(models[["series", "model", "sigma"]], on="series")
    prod = prod[["series", "outlet_id", "product", "date", "forecast", "lo95", "hi95", "model", "sigma"]]
    prod.round({"forecast": 3, "lo95": 3, "hi95": 3}).to_csv(MOUT / "forecast_next28.csv", index=False, date_format="%Y-%m-%d")

    print("=== Holdout (6 Sep - 31 Oct 2026, 56 days x 60 series) ===")
    print(overall.to_string())
    print("\n=== JMP ETS accuracy by segment ===")
    print(by_type.to_string())
    print("\n=== Models JMP selected ===")
    print(models.model.value_counts().to_string())
    print(f"\nforecast_next28: {len(prod)} rows, {prod.date.min().date()} to {prod.date.max().date()}")


if __name__ == "__main__":
    main()
