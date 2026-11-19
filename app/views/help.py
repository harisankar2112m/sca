import streamlit as st

st.title("Help")

st.markdown("""
### Step-by-step
1. **Data** – the app opens with built-in sample data (30 outlets, Apr 2023 – Oct 2026). To use your own data, open
   *Data → Upload your data*, upload the daily sales and outlet master CSVs (optionally current stock) and click
   **Validate and load**. Errors are listed with the row or column to fix.
2. **Sidebar settings** – choose the **target service level** (how sure you want to be that an outlet does not run dry
   before its next delivery) and the **truck trips per day** the depot can send. Every page updates.
3. **Demand Forecast** – pick an outlet and product to see the 28-day forecast with its 95% interval, and how accurate the
   model was on 56 days it had not seen.
4. **Replenishment Planner** – enter today's dip readings (expander at the top), then read the dispatch plan: who is Red /
   Amber / Green, how much to send (in 4 kL compartments), and which orders do not fit on the available trucks.
5. **Scenarios** – choose a preset (diesel surge, festival, strike, fleet cut) or move the sliders; compare KPIs with the base case.
6. **Insights & Export** – the manager briefing, the policy backtest and downloads (dispatch plan CSV, PDF summary).
""")

st.markdown("### Input formats")
st.markdown("""
| File | Columns | Rules |
|---|---|---|
| Daily sales | `date` (YYYY-MM-DD), `outlet_id`, `product` (MS/HSD), `sales_kL`, `closing_stock_kL` | ≥ 2 years per outlet-product; no negatives; no duplicate date × outlet × product |
| Outlet master | `outlet_id`, `outlet_type`, `distance_km`, `transit_days`, `ms_capacity_kL`, `hsd_capacity_kL`, `ms_dead_stock_kL`, `hsd_dead_stock_kL` | dead stock < capacity; transit 1–10 days |
| Current stock | `outlet_id`, `product`, `current_stock_kL`, `as_of_date` | stock ≤ tank capacity; outlets must exist in the master |
""")

st.markdown("### Key terms")
st.markdown("""
| Term | Meaning |
|---|---|
| **Days of cover** | How many days current usable stock (stock − dead stock) lasts at the forecast demand. |
| **Protection period** | Days the outlet must survive if we do not order today: transit time (+ any delay). |
| **Safety stock** | z × forecast uncertainty over the protection period; z comes from the service level (98% → 2.05). |
| **Reorder point (ROP)** | Dead stock + forecast demand over the protection period + safety stock. Order when stock ≤ ROP. |
| **Order quantity** | Free tank space expected when the truck arrives, rounded down to whole 4 kL compartments. |
| **Red / Amber / Green** | Red: will run dry before a truck dispatched tomorrow arrives. Amber: at/below ROP. Green: enough cover. |
| **Priority** | When trucks are short, outlets with the lowest days of cover are served first. |
| **ETS model (e.g. MNM)** | Exponential smoothing: Error / Trend / Season, each A (additive), M (multiplicative) or N (none). |
| **MAPE** | Mean absolute percentage error of the forecast on held-out days. |
""")

st.markdown("### FAQ")
with st.expander("Where does the forecast come from?"):
    st.write("The model was built and validated in JMP (Time Series Forecast platform, ETS models selected by AIC, weekly "
             "season). The built-in forecasts are JMP's exported output. For uploaded data, the app refits the same ETS "
             "family in Python and keeps the lowest-AIC model, because JMP cannot run inside a web app.")
with st.expander("Is the data real?"):
    st.write("Market data (all-India monthly consumption) is real, from PPAC. Outlet-level sales, stock and deliveries are "
             "synthetic because oil companies do not publish them; they are calibrated to PPAC trend and seasonality and "
             "to real events. See Data → Templates & data dictionary.")
with st.expander("Why are days with a dry-out treated differently?"):
    st.write("When an outlet runs dry, recorded sales are lower than what customers wanted. Training a model on those days "
             "would teach it to under-forecast. Such days (closing stock at dead stock) are replaced with the average of the "
             "same weekday over the previous four normal weeks.")
with st.expander("The plan shows orders without a truck — what should I do?"):
    st.write("Those outlets need fuel but the depot's truck limit is used up by more urgent outlets. Options: hire extra "
             "trucks, use a larger truck for multi-product loads, or ask the dealer to ration sales until the next day. "
             "Use Scenarios to see how many extra trips would remove the shortage.")
with st.expander("Why does a higher service level create more orders?"):
    st.write("A higher service level means more safety stock, so reorder points rise and outlets reach them earlier. It "
             "lowers dry-out risk but uses more truck trips — that is the responsiveness vs efficiency trade-off.")
with st.expander("Upload fails — common fixes"):
    st.write("Save as CSV (comma-separated, UTF-8); keep the exact column names from the template; use YYYY-MM-DD dates; "
             "product must be MS or HSD; remove totals rows; make sure every outlet in the sales file is in the outlet master.")
st.caption("DryOut Shield · SCA group project, GIM PGDM-BDA 2026-27 · AI assistance (Claude) was used for coding support and is disclosed in the report.")
