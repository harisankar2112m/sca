# Fuel Supply Chain – Problem Shortlist (input for M1 proposal)

**Course:** Supply Chain Analytics, PGDM-BDA 2026-27, Term 5 · **Sector:** Fuel (India)
**Team:** Sakshi Malwanker (B2025159), Harisankar M (B2025139), George K Manuel (B2025138), Aswin R Nair (B2025129)
**Prepared:** 14 Nov 2026 (desk research; the team should verify every source before citing it)

---

## 1. Context: the Indian fuel supply chain

**Flow:** crude imports (about 90% of consumption is imported, and about half normally passes through the Strait of Hormuz) → refineries → pipelines, rail and coastal transport → terminals and depots → tank trucks (secondary transport) → retail outlets, LPG bottling plants and distributors → consumers.

**Key players:**
- **Public-sector oil marketing companies (OMCs):** IOCL, BPCL and HPCL hold about 90% of retail outlets. IOCL alone runs more than 41,600 stations.
- **Private retailers:** Nayara and Reliance-bp.
- **Others:** tank-truck transporters, outlet dealers, LPG distributors and ethanol distilleries.

**2025-26 backdrop:**
- **Sanctions:** US sanctions on Rosneft and Lukoil took effect on 21 Nov 2025.
- **West Asia war:** the war in 2026 disrupted shipping through Hormuz and pushed Brent above US$100.
- **Price hikes:** the first retail price hike in about four years came on 15 May 2026 (₹3/L), with further hikes on 19 and 24 May.
- **Ethanol:** E20 blending was reached during ESY 2025-26.

---

## 2. Shortlisted problems (ranked)

Each criterion is scored 1–5 (5 = best): **I** = business impact, **U** = urgency, **Q** = quantifiable and data available, **F** = feasible as a course app. **Total** is out of 20.

| Rank | Problem | Who is affected | How it shows up | I | U | Q | F | Total | Method fit |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Retail outlet dry-outs from poor replenishment planning** | OMC depot and territory managers, dealers, motorists | Stock-outs, rationing (₹500–2,000 caps), lost sales, queues | 5 | 5 | 4 | 5 | **19** | Predictive (demand forecast) → reorder / dispatch plan |
| 2 | **LPG refill delays and distributor stock-outs** | LPG distributors, households, hotels | Waits of 25–30+ days, booking caps, black-marketing | 5 | 5 | 3 | 4 | **17** | Predictive + inventory policy; Monte Carlo |
| 3 | **Crude sourcing under sanctions and Hormuz risk** | Refinery procurement, OMCs | Higher landed cost, supply gaps, under-recoveries | 5 | 5 | 3 | 3 | **16** | Prescriptive (supplier-mix LP, stochastic / Monte Carlo) |
| 4 | **Ethanol supply shortfall vs E20 blending mandate** | OMC blending terminals, distilleries | 82.5% of contracted ethanol delivered; seasonal feedstock | 4 | 4 | 3 | 4 | **15** | Prescriptive (multi-period allocation LP) |
| 5 | **Demand shift from EVs and E20: depot capacity planning** | OMC planning teams | Over- or under-built capacity; petrol growth slowing | 4 | 2 | 5 | 4 | **15** (below #4 on urgency) | Predictive (ARIMA/SARIMA + scenarios) |
| 6 | **Secondary transport cost and tank-truck turnaround** | Depot logistics managers, transporters | Long turnaround, idle trucks, high freight cost | 4 | 3 | 3 | 4 | **14** | Prescriptive (routing / allocation) + descriptive KPIs |
| 7 | **Transit losses and pilferage in tank trucks** | Depot managers, dealers | Short deliveries, adulteration | 3 | 2 | 2 | 4 | **11** | Descriptive (KPI / anomaly dashboard) |

### Evidence per problem

**1. Retail outlet dry-outs**
- **May 2026:** highway outlets in six states (Maharashtra, MP, Rajasthan, Bihar, UP and Uttarakhand) rationed fuel because of replenishment delays from depots. Some stocks fell from the usual 25,000–26,000 L to about 13,000 L. Highway and rural outlets, about 29% of the network, are far from depots ([Business Today, 15 May 2026](https://www.businesstoday.in/india/story/highway-fuel-crunch-several-pumps-in-6-states-ration-supply-amid-replenishment-delays-531778-2026-05-15)).
- **Demand shift:** bulk diesel buyers moved to retail pumps because of a price gap of about ₹40/L, causing dry-outs from Punjab to Odisha ([Deccan Chronicle](https://deccanchronicle.com/nation/bulk-consumers-shifting-to-retail-pumps-behind-surge-in-fuel-demand-1958224); [PSU Watch](https://psuwatch.com/newsupdates/petrol-pumps-running-dry-in-india-not-us-say-indian-oil-bpcl-and-hpcl)). Punjab dealers reported frequent dry-outs ([Newswav](https://newswav.com/article/fuel-supply-crisis-hits-punjab-petrol-pumps-dealers-seek-govt-intervention-A2605_NgqMwF)).
- **Earlier episodes:** about 1,000 of 4,900 pumps in Madhya Pradesh went dry in June 2022 ([Hindustan Times via PressReader](https://www.pressreader.com/india/hindustan-times-delhi/20220617/281754157985845); [Business Standard](https://www.business-standard.com/article/economy-policy/india-stares-at-fuel-shortage-with-spike-in-under-recovery-at-omcs-122061501034_1.html)). About 2,000 pumps ran dry during a truckers' strike ([Outlook Business](https://www.outlookbusiness.com/news/about-2000-petrol-pumps-run-dry-as-truckers-strike-against-new-penal-code)).
- **Counter-view:** the government and OMCs say there is no supply shortage and that dry-outs are local or panic-driven ([New Kerala](https://www.newkerala.com/news/a/no-shortage-petrol-diesel-lpg-retail-outlets-govt-526.htm); [Organiser](https://organiser.org/2026/03/25/345722/bharat/no-fuel-shortage-only-panic-how-rumours-triggered-queues-across-cities-in-bharat/amp/)). This actually supports the framing: **the problem is planning and replenishment at outlet level, not national supply.**

**2. LPG refill delays (2026)**
- About 57% of surveyed households reported delays, and some went back to chulhas or kerosene ([Outlook Money](https://www.outlookmoney.com/amp/story/news/57-per-cent-households-revert-to-chulhas-and-kerosene-as-lpg-stress-deepens-worldpanel-report); [Deccan Herald](https://www.deccanherald.com/india/more-than-half-indian-houses-faced-delay-in-getting-lpg-last-week-some-paid-extra-to-buy-cylinders-says-survey-3930912)).
- Waits ran past 30 days in some cities ([OneIndia](https://www.oneindia.com/bengaluru/lpg-crunch-pushes-cylinder-waiting-period-beyond-30-days-in-cities-8064629.html)). The minimum gap between bookings was raised from 21 to 25 days ([The Hitavada](https://www.thehitavada.com/Encyc/2026/4/8/25-day-cap-on-lpg-cylinder-booking-hits-households.html)).
- Booking systems crashed during the demand surge ([Sunday Guardian](https://sundayguardianlive.com/india/lpg-gas-shortage-latest-news-lpg-cylinder-booking-systems-crash-across-india-amid-demand-surge-apps-ivrs-whatsapp-services-down-check-indane-bharat-gas-hp-gas-helpline-numbers-176083/)). Commercial supply was rationed in favour of hospitals and schools ([Brut](https://www.brut.media/in/articles/commercial-lpg-shortage-in-india-explained)).
- **Counter-view:** Alt News describes it as partly panic-driven ([Alt News](https://www.altnews.in/indias-lpg-crisis-real-supply-crunch-or-war-driven-panic-alt-news-checks-the-last-mile/)).

**3. Crude sourcing risk**
- Russia supplied about a third of India's crude (about 1.7 mb/d) in 2025, of which about 1.2 mb/d came from Rosneft and Lukoil. These two were sanctioned from 21 Nov 2025 ([S&P Global](https://www.spglobal.com/energy/en/news-research/latest-news/crude-oil/102425-india-stares-at-crude-sourcing-challenge-after-us-sanctions-rosneft-lukoil); [Gulf News](https://gulfnews.com/business/energy/us-sanctions-on-rosneft-lukoil-threaten-indian-refiners-russian-oil-supply-1.500318540)). Later flows were contested ([bne IntelliNews](https://www.intellinews.com/india-s-russian-oil-imports-a-complex-picture-of-contradictory-claims-416989/)).
- The 2026 Hormuz disruption led to price hikes. The ₹3/L hike covered only about one-tenth of OMC losses ([Al Jazeera](https://www.aljazeera.com/amp/economy/2026/5/15/india-hikes-fuel-prices-as-iran-crisis-bites); [Outlook Money](https://www.outlookmoney.com/news/petrol-diesel-gas-prices-hiked-again-iran-us-tensions-continue-to-choke-strait-of-hormuz); [Business Today](https://www.businesstoday.in/latest/economy/story/fuel-price-hike-sparks-ripple-effect-across-sectors-as-crude-oil-shock-reaches-india-531675-2026-05-15)).
- **Feasibility caveat:** this is a national or refinery-level decision with confidential cost data, so it is harder to scope as a course app.

**4. Ethanol supply vs E20**
- OMCs received 987 crore L of ethanol against 1,197 crore L contracted in ESY 2025-26, or 82.5% ([Business Standard – ethanol](https://www.business-standard.com/topic/ethanol)). There are disputes over the tender allocation, and some feedstocks were barred for 2026-27.
- Logistics depend on rail and road tankers, and depots need upgrades for blending ([KPMG, *Beyond E20*, 2026](https://kpmg.com/in/en/insights/2026/06/beyond-e20-repositioning-ethanol-as-indias-transport-energy-backbone.html); [NITI Aayog roadmap](https://niti.gov.in/sites/default/files/2023-02/EthanolBlendingInIndia_compressed.pdf)).
- The government has rejected selling multiple blend grades at pumps because of the cost of parallel supply chains ([AutocarPro](https://www.autocarpro.in/news/indias-shift-to-e20-was-more-than-two-decades-in-the-making-centre-133536)).

**5. EV and E20 demand shift**
- The IEA projects India's oil demand at 6.6 mb/d by 2030, up from 5.5 mb/d in 2023. Petrol growth is slowing to about 0.7% a year because of electrification, while diesel drives about half of demand growth ([ThePrint, IEA](https://theprint.in/economy/india-to-drive-growth-in-oil-demand-till-2030-transport-fuels-main-reason/2129441); [Argus](https://www.argusmedia.com/de/news-and-insights/latest-market-news/2537175-india-ev-growth-to-hit-gasoline-demand-iea-correction)).
- S&P Global cut its 2030 EV share forecast from 22% to 18.5% ([AutocarPro](https://www.autocarpro.in/news/sp-global-cuts-india-ev-forecast-from-22-to-185-by-2030-122671)).

**6. Secondary transport and turnaround**
- An academic study of tank-truck turnaround time at an Indian OMC found bottlenecks in the process ([Pacific Business Review, 2023](https://www.pbr.co.in/2023/june9.aspx)).
- OMCs mandate GIS route mapping and vehicle tracking ([BPCL transport discipline guidelines](https://www.bharatpetroleum.in/pdf/transport-discipline-guidelines-83ac38.pdf)).
- **Gap:** no public data on freight cost per kL, so cost parameters would have to be estimated.

**7. Pilferage**
- OMCs report no pilferage from GPS-fitted trucks ([Lok Sabha reply](https://eparlib.sansad.in/bitstream/123456789/539564/1/39588.pdf)). Most other loss figures come from vendor blogs and are unverified, so the evidence is weak.

---

## 3. Data availability

| Source | What it gives | Notes |
|---|---|---|
| [PPAC – product-wise consumption](https://ppac.gov.in/consumption/products-wise) | Monthly all-India consumption by product (MS/petrol, HSD/diesel, LPG, ATF …), '000 tonnes | Years 2023-24 to 2026-27 shown online; **historical report needs free registration**. Long monthly history is needed for the ≥36-month rule. |
| [PPAC – state-wise](https://ppac.gov.in/consumption/state-wise) | State-wise POL sales (xlsx) | Granularity (monthly or annual) to be checked after download |
| [data.gov.in – Monthly consumption of petroleum products](https://data.gov.in/resource/monthly-consumption-petroleum-products) / [AIKOSH](https://aikosh.indiaai.gov.in/home/datasets/details/monthly_consumption_of_petroleum_products.html) | Open monthly product-wise series | Good for a longer history |
| PPAC monthly Industry Consumption Review (PDF), e.g. [Feb 2024](https://ppac.gov.in/uploads/rep_studies/1711109718_Industry-Consumption-Report-February-2024.pdf) | Monthly growth by product and segment | Context and validation |
| Outlet-level sales, tank capacity, depot distances | Not public | **Synthetic.** Calibrate to PPAC totals and the facts above (25–26 kL tanks, highway vs urban mix, seasonality, demand shocks), and disclose the method (Guidelines §7) |

---

## 4. Recommendation for the M1 proposal

**Select Problem 1: "Preventing retail-outlet dry-outs through demand forecasting and replenishment planning".** Problem 2 (LPG distributors) is a close alternative with the same analytics design.

- **Decision maker:** OMC depot or territory sales manager, plus outlet dealers.
- **Decision:** when and how much to replenish each outlet (tank-truck dispatch), and which outlets to prioritise during a demand surge.
- **Strategy fit:** a responsive supply chain at outlets, especially highway and rural ones, balanced against efficient use of depots and trucks.
- **Core method:** predictive, CLO 4.
  - Weekly or daily demand forecasts per outlet and product (benchmark, exponential smoothing and SARIMA), with validation through MAPE and holdout tests.
  - Forecast uncertainty then sets safety stock, reorder points and days-of-cover alerts.
  - An optional prescriptive add-on is a tank-truck allocation when trucks are scarce.
- **Data:**
  - PPAC monthly product consumption, real data, used for national and state trend and seasonality.
  - Synthetic outlet-level weekly sales for at least 104 weeks, generated from PPAC patterns plus outlet type, a price-gap demand shock and holidays, and disclosed in the report.
- **App:**
  - Upload or use the sample outlet data.
  - Choose an outlet and product.
  - See the forecast with intervals, days of cover, a dry-out risk flag, recommended reorder quantity and date, and a downloadable dispatch plan.
  - Scenario sliders for a demand surge or a lead-time delay.

**Why this one:**
- It is current: the six-state crunch in May 2026 and the bulk-to-retail shift.
- It is clearly quantifiable.
- Real public data exists at aggregate level.
- It fits the forecasting part of the course directly.
- It is feasible within the term, and there is an obvious manager who would use the app.

**Open points for the team:**
1. Verify the sources, especially 2026 news items, and replace weak ones with OMC annual reports or PPAC documents where possible.
2. Register on PPAC and check how far back the monthly product-wise and state-wise data goes.
3. Decide between outlet replenishment (Problem 1) and LPG distribution (Problem 2).
