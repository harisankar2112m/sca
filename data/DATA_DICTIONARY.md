# DryOut Shield – Data Dictionary

**Period covered:** 1 Apr 2023 – 31 Oct 2026, which is 43 months or 1,310 days. The guidelines require at least 36 months.
**Units:** kL = kilolitre (1,000 litres). TMT = thousand metric tonnes.
**Products:** MS = motor spirit (petrol). HSD = high-speed diesel.

## 1. Real vs synthetic (disclosure, Guidelines §7)

| File | Real or synthetic | How it was produced |
|---|---|---|
| `ppac_monthly_ms_hsd.csv` | **Real, public** | Downloaded from PPAC's products-wise consumption page by `src/fetch_ppac.py` |
| `outlets.csv` | **Synthetic** | `src/generate_outlet_data.py`, fixed seed 2026 |
| `outlet_daily_sales.csv` | **Synthetic**, calibrated to PPAC | same |
| `deliveries_asis.csv` | **Synthetic** (simulated current practice) | same |
| `events_calendar.csv` | Real dates. The demand effects are assumptions | same |
| `synthetic_generator_parameters.csv` | Synthetic ground truth | same. **Not an app input** |

**Why outlet data is synthetic:** OMCs do not publish outlet-level daily sales, stock, tank sizes or lead times. To keep the synthetic data realistic:
- Each outlet's demand follows the real PPAC monthly trend and seasonality. Monthly synthetic totals correlate with PPAC at 0.99 for MS and 0.95 for HSD.
- Real event dates are used: festivals, the Jan 2024 truckers' strike, and the 2026 bulk-to-retail diesel shift.
- Tank sizes are set from news facts, e.g. usual highway outlet stock of about 25–26 kL.

## 2. `ppac_monthly_ms_hsd.csv` – market data (real)

| Column | Type | Description |
|---|---|---|
| `month` | YYYY-MM | Calendar month |
| `financial_year` | text | Indian FY (April–March), e.g. 2025-2026 |
| `product` | MS / HSD | Product |
| `consumption_tmt` | number | All-India domestic consumption, '000 metric tonnes |
| `ppac_updated` | DD-MM-YYYY | Date PPAC last updated the figure. Recent months are provisional |
| `days_in_month` | integer | Days in the month |
| `consumption_million_litres` | number | `consumption_tmt` ÷ density. MS uses 0.745 kg/L and HSD 0.832 kg/L, so 1 TMT ÷ density gives million litres |
| `per_day_tmt` | number | `consumption_tmt` ÷ `days_in_month`. Used to build the daily market index |

## 3. `outlets.csv` – outlet master (one row per outlet, 30 rows)

| Column | Type | Description | Range in sample data |
|---|---|---|---|
| `outlet_id` | text | U-xx = urban, H-xx = highway, R-xx = rural | U-01…U-12, H-01…H-10, R-01…R-08 |
| `outlet_type` | Urban / Highway / Rural | Segment | 12 / 10 / 8 |
| `distance_km` | integer | Road distance from the depot | 5–40 / 60–180 / 80–220 |
| `transit_days` | integer | Days from dispatch to arrival | 1 urban, 1–2 highway, 2 rural |
| `ms_capacity_kL`, `hsd_capacity_kL` | number | Total underground tank capacity per product | MS 10–30, HSD 20–60 |
| `ms_dead_stock_kL`, `hsd_dead_stock_kL` | number | Unpumpable residual stock, 5% of capacity | — |

## 4. `outlet_daily_sales.csv` – daily outlet × product records (78,600 rows)

| Column | Type | Description | Visible in real outlet data? |
|---|---|---|---|
| `date` | YYYY-MM-DD | Business day | yes |
| `outlet_id` | text | Links to `outlets.csv` | yes |
| `product` | MS / HSD | Product | yes |
| `opening_stock_kL` | number | Stock at start of day, before receipts | yes (dip reading) |
| `receipt_kL` | number | Fuel received from the depot that morning | yes |
| `sales_kL` | number | Fuel sold. **Censored**: on a dry-out day it is less than demand | yes |
| `closing_stock_kL` | number | = opening + receipt − sales | yes |
| `true_demand_kL` | number | What customers wanted to buy | **no – synthetic only**, used to score policies |
| `lost_sales_kL` | number | = true demand − sales | no (only estimable) |
| `dry_out` | 0/1 | 1 if any demand was lost that day (lost > 0.05 kL) | partly (dealer log) |

## 5. `deliveries_asis.csv` – simulated current (reactive) replenishment

The simulated current practice works as follows:
- The dealer raises an indent when closing stock falls below a fixed share of tank capacity: 35% urban, 50% highway, 55% rural.
- The indent asks to fill the tank, in 4 kL compartments.
- The depot has **34 tank-truck trips per day** (20 kL each) and dispatches first-come-first-served.
- Each trip has an 8% chance of a 1-day delay.
- No trucks are dispatched during the strike (1–3 Jan 2024).

| Column | Description |
|---|---|
| `indent_date` | Day the dealer raised the indent (end of day) |
| `outlet_id`, `product` | Who ordered what |
| `indent_kL` | Quantity ordered (multiple of 4 kL) |
| `dispatch_date` | Day the truck left the depot (waits in queue when trips are exhausted) |
| `arrival_date` | Day the fuel was received (start of day) |
| `trips` | Truck trips used, = ceil(indent_kL / 20) |
| `received_kL` | Quantity actually decanted. Can be less than the indent if the tank had no room. Blank for 39 loads still in transit on 31 Oct 2026 |
| `lead_time_days` | arrival_date − indent_date (mean 1.6, max 6 days) |

**Resulting "as-is" performance:**
- About 3% of outlet-days are dry-outs in a normal month.
- About 12% during the May–Jun 2026 diesel shift.
- About 41% during the Jan 2024 strike.
- Highway outlets are dry about 10% of days. Urban outlets are dry about 1–4% of days.
- This is the baseline the app's forecast-driven policy must beat.

## 6. `events_calendar.csv` – demand events used by the generator

| Column | Description |
|---|---|
| `event` | Diwali run-up, Diwali day, Post-Diwali lull, Dussehra, Holi, Truckers' strike – panic buying, Bulk-to-retail diesel shift, Harvest season |
| `start`, `end` | Inclusive date window |
| `outlet_types`, `products` | Which outlets and products are affected |
| `demand_multiplier` | Multiplier on normal demand. The diesel shift ramps up to its peak (+30%) and back down |
| `note` | Reason |

## 7. How demand was generated

**demand = base × market index × weekday factor × event factor × outlet drift × noise**

| Component | Basis |
|---|---|
| base | Outlet size by type (kL/day at FY2023-24 level): Urban MS 4–8 / HSD 4–8; Highway MS 2–4 / HSD 8–14; Rural MS 1–2.5 / HSD 2.5–5 |
| market index | PPAC per-day consumption ÷ FY2023-24 average, interpolated daily. Real trend and seasonality, e.g. the monsoon diesel dip |
| weekday factor | Urban MS peaks Fri–Sat, diesel dips on Sunday; rural outlets get a +18% weekly market day |
| outlet drift | Each outlet grows ±3%/yr relative to the market |
| noise | AR(1) log-normal (φ = 0.3). Standard deviation is 7% urban, 10% highway, 13% rural |

## 8. Upload templates (`templates/`)

| File | Columns | Used on app page |
|---|---|---|
| `template_daily_sales.csv` | date, outlet_id, product, sales_kL, closing_stock_kL | Data / Demand Forecast |
| `template_outlets.csv` | same columns as `outlets.csv` | Data / Replenishment Planner |
| `template_current_stock.csv` | outlet_id, product, current_stock_kL, as_of_date | Replenishment Planner |

**Validation rules the app will apply:**
- Required columns must be present.
- Dates must parse.
- `product` must be MS or HSD.
- Values must not be negative.
- Stock must not exceed tank capacity.
- No duplicate date × outlet × product rows.
- At least 2 years of history per series to fit seasonal models.

## 9. Reproduce

```bash
python src/fetch_ppac.py            # refresh real PPAC data (internet needed)
python src/generate_outlet_data.py  # rebuild all synthetic files (seed 2026)
```
