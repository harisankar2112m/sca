# DryOut Shield – Forecasting Model (built in JMP)

## What the model does
The model forecasts daily demand (kL) for each of **60 series**: 30 outlets, each selling petrol (MS) and diesel (HSD). It gives a 95% forecast interval for every day.

The replenishment logic uses these forecasts and their uncertainty:
- days of cover
- reorder point (ROP)
- truck loads
- truck priority

## Tool and method
| Item | Choice |
|---|---|
| Software | **JMP Student Edition 19** (JMP Pro features) |
| Platform | Analyze › Specialized Modeling › **Time Series Forecast**, run once for each series (`By(:series)`) |
| Model family | Exponential smoothing (ETS) state-space models: error × trend × season, each additive or multiplicative, with optional damping |
| Selection | JMP fits its recommended set of ETS models and keeps the one with the lowest **AIC** for each series |
| Seasonality | 7 days. JMP's time-pattern analysis also suggests 7 |
| Response | `demand_kL`, which is sales with dry-out days corrected (see below) |
| Validation | Fit on data up to 5 Sep 2026, then forecast the **56-day holdout** (6 Sep – 31 Oct 2026). Compare against two benchmarks |
| Production | Refit on all data (Apr 2023 – Oct 2026), then forecast **1–28 Nov 2026** |

**Correcting dry-out days.** On a dry-out day the outlet ran out, so recorded sales understate demand. On those days we replace sales with the average for the same weekday over the previous four normal weeks. This recovers 87% of the true lost demand: 10,581 kL of the 12,091 kL lost, which can be checked here only because the data is synthetic.

## Results (holdout: 56 days × 60 series)
| Method | MAPE | RMSE (kL) | Bias | Series won (MAPE) | 95% interval coverage |
|---|---|---|---|---|---|
| **JMP Time Series Forecast (ETS)** | **10.4%** | **0.79** | −5.4% | **41 / 60** | **95.3%** |
| Benchmark: 28-day moving average | 10.9% | 0.83 | −5.3% | 15 / 60 | – |
| Benchmark: seasonal naive (same weekday last week) | 12.4% | 0.91 | −5.1% | 4 / 60 | – |

**How to read these results**
- **JMP beats both benchmarks** on every error metric.
- **The 95% intervals are well calibrated:** 95.3% of actual values fall inside them. This matters most, because safety stock is based on these intervals.
- **Forecasts run low by about 5% in the holdout.** Demand in Sep–Oct 2026 rose faster than the trend: PPAC shows diesel up about 12% year on year in October. All three methods share this bias. The app's Scenarios page should therefore offer a demand-surge uplift.
- **Accuracy by segment:**
  - Urban MS is the easiest to forecast: 6.0% MAPE.
  - Rural HSD is the hardest: 17.7% MAPE, because of harvest spikes and high noise.
  - This is why rural outlets need more safety stock.
- **Models JMP selected:**
  - MNM (multiplicative error, no trend, multiplicative season): 39 series
  - MNA (multiplicative error, additive season): 15 series
  - ANA (additive error, additive season): 6 series
- **No trend term was selected.** The level smoothing weight (alpha, about 0.1–0.2) tracks slow growth instead.

## Files
| File | What it is |
|---|---|
| `src/prepare_jmp_input.py` | Builds `jmp/model_input.csv`: one row per series × day, the dry-out correction, and the Train/Holdout split |
| `jmp/DryOut_Forecast_Model.jsl` | **The JMP model script.** Runs the validation and production fits and saves all outputs |
| `jmp/DryOut_model_input.jmp` | JMP data table, with the model saved as a table script so it can be re-run from inside JMP |
| `jmp/out/validation_forecasts.csv`, `production_forecasts.csv` | Forecasts exported by JMP, with 95% limits |
| `jmp/out/validation_models.txt`, `production_models.txt` | JMP report text for each series: model type, AIC, parameter estimates |
| `jmp/out/chart_*.png` | JMP forecast charts for the report (H-03 HSD, U-01 MS, R-02 HSD) |
| `src/evaluate_jmp_model.py` | Scores the JMP forecasts on the holdout and packages the results |
| `model/model_comparison.csv`, `holdout_by_series.csv` | Validation tables for report section 5 |
| `model/jmp_models.csv` | The model JMP chose for each series, with AIC, sigma and smoothing weights |
| `model/forecast_next28.csv` | **Production forecast used by the app**: series, date, forecast, lo95, hi95 |

## How to reproduce
```bash
python src/fetch_ppac.py              # real PPAC market data
python src/generate_outlet_data.py    # synthetic outlet data (seed 2026)
python src/prepare_jmp_input.py       # modelling table for JMP
```

Then open `jmp/DryOut_Forecast_Model.jsl` in JMP and run it with ⌘R. It takes about 2 minutes.

Finally, score the forecasts:
```bash
python src/evaluate_jmp_model.py
```

## How the app will use the JMP model
- **Built-in sample data:** the app reads `model/forecast_next28.csv` and `model/jmp_models.csv` directly. These are JMP's own forecasts and intervals.
- **Replenishment logic** (ROP, truck loads, truck limit K, priority ranking, scenarios) is computed in the app from the JMP forecasts. It is a set of decision rules, not a statistical model.
- **User-uploaded data:** JMP cannot run inside a web app. For new data the app refits the same ETS model that JMP selected for that series in Python (statsmodels `ETSModel`), and checks it against JMP's results. Re-running the JSL in JMP and uploading its forecast file is also supported.
