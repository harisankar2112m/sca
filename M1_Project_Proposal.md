# M1 Project Proposal – DryOut Shield: Forecast-Driven Replenishment for Fuel Retail Outlets

**Course:** Supply Chain Analytics (PGDM-BDA 2026-27, Term 5) · **Instructor:** Prof. Prasad Patil
**Sector:** Fuel (India) · **Group members:**

| Name | Roll no. |
|---|---|
| Sakshi Malwanker | B2025159 |
| Harisankar M | B2025139 |
| George K Manuel | B2025138 |
| Aswin R Nair | B2025129 |

*Draft for team review. The full shortlist and sources are in `M1_Fuel_Problem_Shortlist.md`.*

---

## 1. Problem identification (Guidelines §4.1–4.2)

We studied the Indian fuel supply chain using news, government data (PPAC), and IEA, KPMG and NITI Aayog reports. We shortlisted seven current problems and ranked them on business impact, urgency, data availability and feasibility (score out of 20):

| Rank | Problem | Score |
|---|---|---|
| **1** | **Retail-outlet dry-outs caused by poor replenishment planning** | **19** |
| 2 | LPG refill delays and distributor stock-outs | 17 |
| 3 | Crude sourcing under sanctions and Strait of Hormuz risk | 16 |
| 4 | Ethanol supply shortfall vs the E20 blending mandate | 15 |
| 5 | Demand shift from EVs and E20 (depot capacity planning) | 15 |
| 6 | Secondary transport cost and tank-truck turnaround | 14 |
| 7 | Transit losses and pilferage | 11 |

**Why we selected Problem 1**
- **Current, with evidence.** In May 2026, highway outlets in six states (Maharashtra, MP, Rajasthan, Bihar, UP, Uttarakhand) rationed fuel to ₹500–2,000 per vehicle while waiting for tank trucks. Some outlet stocks fell to about 13 kL from the usual 25–26 kL. Highway and rural outlets, about 29% of the network, sit far from depots ([Business Today, 15 May 2026](https://www.businesstoday.in/india/story/highway-fuel-crunch-several-pumps-in-6-states-ration-supply-amid-replenishment-delays-531778-2026-05-15)).
- **Demand shocks.** A price gap of about ₹40/L shifted bulk diesel buyers to retail pumps, which led to dry-outs from Punjab to Odisha ([Deccan Chronicle](https://deccanchronicle.com/nation/bulk-consumers-shifting-to-retail-pumps-behind-surge-in-fuel-demand-1958224); [PSU Watch](https://psuwatch.com/newsupdates/petrol-pumps-running-dry-in-india-not-us-say-indian-oil-bpcl-and-hpcl)). In June 2022, about 1,000 of Madhya Pradesh's 4,900 pumps ran dry ([Hindustan Times](https://www.pressreader.com/india/hindustan-times-delhi/20220617/281754157985845)).
- **The government says there is no national shortage.** That points to the real gap: *outlet-level demand anticipation and replenishment*, not national supply.
- **Quantifiable, with data:** sales, stock, tank capacity and lead time are all measurable. PPAC publishes monthly product consumption.
- **Fit with the course:** time-series forecasting (CLO 4) that drives an inventory decision.
- **Decision-oriented:** there is a clear user, the depot or territory manager.

---

## 2. Problem statement

> Fuel retail outlets served by an OMC depot run dry when demand rises or deliveries are delayed. The main causes are demand spikes (harvest, festivals, price-gap shifts) and long depot-to-outlet lead times, especially for highway and rural outlets. Replenishment today is largely reactive: dealers place indents when stock looks low. **We will build a decision-support web app that forecasts each outlet's daily petrol (MS) and diesel (HSD) demand, converts the forecast and its uncertainty into days-of-cover and dry-out-risk alerts, and recommends when and how much to replenish, in tank-truck loads.** When trucks are scarce, the app also recommends which outlets to serve first.

---

## 3. Supply chain context and strategy (CLO 1)

**Supply chain.** Crude imports → refinery → pipeline, rail or coastal transport → OMC depot or terminal → tank trucks (secondary transport) → retail outlet (underground tanks) → motorists, farmers and transporters.

- **Players:** OMCs (IOCL, BPCL and HPCL hold about 90% of outlets), depot planners, tank-truck transporters, dealers and customers.
- **Flows:**
  - **Material:** fuel.
  - **Information:** indents, dip readings or automation data, GPS truck tracking.
  - **Money:** dealer prepayment to the OMC, freight paid to transporters.
- **Decisions we address:** outlet inventory and replenishment, and secondary distribution scheduling.

**Strategy fit**
- **Business strategy:** OMCs compete on availability, because a dry outlet loses the sale to a competitor and damages the brand. Public-sector OMCs also carry a social mandate for uninterrupted supply.
- **Supply chain strategy:**
  - **Responsive** at the retail end, for highway and rural outlets and during demand surges.
  - **Efficient** in secondary transport: full truck loads and limited trucks.
  - The app manages this trade-off with risk-based replenishment rather than "fill everyone, every day".
- **Trade-offs and risks:**
  - Higher safety stock is limited by tank capacity (ullage) and blocks dealer working capital.
  - Frequent part-loads raise freight cost.
  - Forecast error, lead-time variability, strikes and price-driven demand shifts are the main risks.

The report and the app's "About" page will also include:
- **System map / causal loop diagram:** demand shock → stock depletion → indent → truck availability → lead time → dry-out → lost sales and panic buying (a reinforcing loop).
- **Business architecture sketch:** where outlet sales data, forecasts and alerts plug into the depot's daily dispatch decision.

---

## 4. Quantitative problem framing (CLO 2)

**Indices:** outlet *i*, product *p* ∈ {MS, HSD}, day *t*.

**Inputs and data**
- Historical daily sales *dᵢₚₜ* (kL).
- Current stock *Sᵢₚ*.
- Tank capacity *Cᵢₚ*.
- Minimum (dead) stock *mᵢₚ*.
- Lead time from the depot *Lᵢ* (days), plus its variability.
- Truck compartment sizes (e.g. 4, 8, 12 or 20 kL).
- Daily truck availability *K*.
- Target service level (e.g. 98%).

**Predictive step (core).** Forecast *D̂ᵢₚₜ* for the next 14–28 days, together with the forecast error σ.

**Decision variables**
- Replenishment quantity *Qᵢₚₜ*, in whole compartment loads.
- Dispatch day *tᵢ*.
- Priority rank under the truck limit.

**Objective.** Keep the probability of dry-out below 1 − service level while using the fewest truck trips. Equivalently, minimise expected dry-out days plus trip cost.

**Rules and constraints**
- **Reorder point:** *ROPᵢₚ = mᵢₚ + D̂ over (Lᵢ + review period) + z·σ_L*.
- **Order condition:** when stock *Sᵢₚ ≤ ROPᵢₚ*, order *Qᵢₚ = Cᵢₚ − (Sᵢₚ − D̂ during Lᵢ)*, rounded down to whole compartment loads.
- **Tank capacity:** stock on arrival plus *Q* must not exceed *Cᵢₚ*.
- **Truck limit:** at most *K* trucks per day. When demand for trucks exceeds *K*, outlets are ranked by **days-of-cover** (*Sᵢₚ / D̂ᵢₚ*) and dry-out probability.

**Assumptions**
- Single depot.
- Deterministic depot supply.
- Lead time varies by outlet type.
- Outlet-level data is synthetic (see §5).

**Method justification**
- Demand shows trend, weekly and annual seasonality, and shocks, so time-series models fit.
- We will compare a benchmark (seasonal naive) with exponential smoothing (ETS / Holt-Winters) and SARIMA.
- Models are validated on a holdout period (MAPE, RMSE and bias), and the best model is selected per outlet.
- Forecast intervals carry the uncertainty through to safety stock.

**Limitations**
- Synthetic outlet data.
- No real-time automation feed.
- Depot stock-outs are not modelled.
- Truck routing is simplified to a count of trucks.

---

## 5. Data plan (Guidelines §7)

| Data | Source | Use |
|---|---|---|
| Monthly consumption of MS and HSD, all-India and state | [PPAC – product-wise](https://ppac.gov.in/consumption/products-wise), [PPAC – state-wise](https://ppac.gov.in/consumption/state-wise), [data.gov.in](https://data.gov.in/resource/monthly-consumption-petroleum-products) (real, public) | Trend and monthly seasonality indices; a "market view" forecast with at least 36 months |
| Daily sales for about 30 outlets, MS and HSD, Apr 2023 – Oct 2026 (more than 1,300 days, about 190 weeks) | **Synthetic**, generated by the team (disclosed) | Outlet-level forecasting and replenishment |
| Tank capacities, dead stock, lead times, truck sizes, freight per trip | Estimated from news facts (25–26 kL tanks, highway/rural share) and OMC norms; basis stated | Replenishment parameters |

**How the synthetic outlet data will be generated**
- **Outlet types:** urban, highway and rural outlets, each with a base volume.
- **Pattern:** a weekly pattern, multiplied by the PPAC monthly seasonality index, multiplied by trend.
- **Events:** harvest and festival spikes, a price-gap demand shock in 2026 (bulk diesel moving to retail), and a truckers'-strike lead-time disruption.
- **Noise:** random noise is added.

The generator script, its parameters and a data dictionary will be submitted. No confidential or personal data is used.

---

## 6. Planned app features (Guidelines §6)

**Platform:** Python + **Streamlit**, deployed on Streamlit Community Cloud (a public URL, no login). Models use `statsmodels`, and charts use Plotly.

| Page | Features |
|---|---|
| **About / Context** | Supply chain description, strategy fit, system map, business architecture, assumptions and limitations, technology outlook |
| **Data** | Built-in sample dataset; CSV upload with validation (columns, dates, negative or missing values, ranges) and clear error messages; downloadable blank template |
| **Demand Forecast** | Choose outlet and product, horizon and models. Shows model comparison (MAPE/RMSE on holdout), forecast chart with 80/95% intervals, and a market view (PPAC monthly forecast) |
| **Replenishment Planner** | Enter current stock (or upload a dip file). Shows days-of-cover, dry-out risk (red/amber/green), reorder point, recommended quantity in truck loads and dispatch date. Truck-constrained priority list for the depot |
| **Scenarios** | Sliders for a demand surge (+x%), lead-time delay (+y days), fewer trucks and service level. KPIs and alerts update live |
| **Insights and Export** | Manager-ready recommendations ("Dispatch 12 kL HSD to Outlet H-07 today – dry-out expected in 1.4 days"); KPI tiles (outlets at risk, expected dry-out days, trips needed); CSV dispatch plan and PDF summary download |
| **Help** | Step-by-step guide, input formats, FAQ |

**Expected outputs:** a validated forecast per outlet and product, a daily dispatch and priority plan, dry-out risk alerts, and scenario comparisons.

---

## 7. Technology outlook (CLO 6), to be expanded in the report

- **IoT tank automation:** automatic tank gauging gives live stock levels, which would feed the app in real time.
- **AI/ML forecasting:** gradient-boosting models with weather, price and event features.
- **Agentic AI:** auto-raising indents and booking trucks within approval limits.
- **Digital twin:** a twin of the depot and outlet network, to stress-test disruptions.

The report will also cover data privacy, dealer trust, and over-reliance on automation.

---

## 8. Plan and responsibilities (tentative)

| Phase | Work | Lead |
|---|---|---|
| Weeks 1–2 | Finalise proposal, PPAC data download, synthetic data generator | Harisankar, George |
| Weeks 2–3 | Forecast models and validation | Harisankar, Aswin |
| Weeks 3–4 | Replenishment logic, scenarios, Streamlit app | George, Aswin |
| Weeks 4–5 | Context and strategy, system map, technology outlook, report | Sakshi |
| Week 5 | Testing, deployment, user guide, AI-use disclosure | All |

*Roles to be confirmed by the team.*

---

## 9. AI use (to be detailed in the report appendix)

AI tools (Claude) were used for desk research support and for drafting this proposal. The team will verify all sources and numbers, and will disclose the tool, purpose and extent of assistance, as required by Guidelines §9.
