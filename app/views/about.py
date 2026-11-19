import streamlit as st

from core.data import load_ppac

st.title("⛽ DryOut Shield")
st.subheader("Preventing fuel-outlet dry-outs with demand forecasting and truck-constrained replenishment")

c1, c2 = st.columns([3, 2])
with c1:
    st.markdown("""
**The problem.** Retail fuel outlets served from an oil-company depot run dry when demand spikes
(harvest, festivals, bulk diesel buyers shifting to retail pumps) or when tank trucks arrive late. Highway and
rural outlets, far from the depot, are hit hardest: in May 2026 highway pumps in six states rationed fuel while waiting
for trucks, even though national supply was adequate. The gap is **outlet-level demand anticipation and replenishment**.

**Who uses this app.** The depot / territory sales manager who decides every evening *which outlets get a truck tomorrow
and how much fuel to send*.

**What it does**
1. Forecasts each outlet's daily petrol (MS) and diesel (HSD) demand for 28 days, with 95% intervals (model built in **JMP**).
2. Converts stock + forecast + delivery time into **days of cover, dry-out risk, reorder point and order quantity** in 4 kL compartments.
3. Allocates the depot's limited trucks to the most urgent outlets and flags outlets that will be left short.
4. Tests scenarios (demand surge, truck delays, fewer trucks) and exports a dispatch plan (CSV/PDF).
""")
with c2:
    st.info("""**How to use (2 minutes)**
1. **Data** – keep the built-in sample or upload your own files.
2. **Demand Forecast** – check the forecast and its accuracy.
3. **Replenishment Planner** – enter today's dip readings; see who needs fuel.
4. **Scenarios** – stress-test the plan.
5. **Insights & Export** – download the dispatch plan.

Planning settings (service level, trucks per day) are in the sidebar.""")
    st.caption("Group: Sakshi Malwanker (B2025159) · Harisankar M (B2025139) · George K Manuel (B2025138) · "
               "Aswin R Nair (B2025129) — Supply Chain Analytics, GIM PGDM-BDA 2026-27, Term 5")

t1, t2, t3, t4, t5 = st.tabs(["Supply chain & strategy", "System map", "Business architecture",
                              "Assumptions & limitations", "Technology outlook"])
with t1:
    st.markdown("""
**Supply chain.** Crude imports → refinery → pipeline / rail / coastal → **OMC depot** → **tank trucks** (secondary
transport) → **retail outlet** underground tanks → motorists, transporters, farmers.

| | |
|---|---|
| **Players** | Oil marketing companies (IOCL, BPCL, HPCL ≈ 90% of outlets), depot planners, transporters, dealers, customers |
| **Material flow** | Petrol and diesel, depot → outlet in 4 kL truck compartments |
| **Information flow** | Dealer indents, daily dip (stock) readings, truck GPS, sales |
| **Money flow** | Dealer prepays the OMC; OMC pays freight to transporters |
| **Decisions supported** | Outlet replenishment (when, how much), daily truck allocation |

**Strategy fit.** OMCs compete on **availability**: a dry outlet loses the sale to a rival pump and damages the brand, and
public-sector OMCs carry a mandate for uninterrupted supply. The supply chain must therefore be **responsive at the
retail end** (especially highway/rural outlets and during surges) while staying **efficient in secondary transport**
(full compartments, limited trucks). DryOut Shield manages this trade-off with *risk-based* replenishment instead of
"fill everyone every day" or "wait for the dealer's indent".

**Trade-offs.** More safety stock is limited by tank size (ullage) and dealer working capital; frequent part-loads raise
freight cost; forecast error, delivery delays, strikes and price-driven demand shifts are the main risks.
""")
with t2:
    st.markdown("**Causal loop: why dry-outs spread** (R = reinforcing loop, B = balancing loop)")
    st.graphviz_chart("""
digraph {
  rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#eef3fb", fontname="Helvetica", fontsize=11];
  edge [fontname="Helvetica", fontsize=10];
  shock [label="Demand shock\\n(harvest, festival,\\nprice gap)"]; dep [label="Outlet stock\\ndepletion"];
  indent [label="Indents to depot"]; trucks [label="Truck\\navailability"]; lt [label="Delivery\\nlead time"];
  dry [label="Dry-outs", fillcolor="#fbe3e3"]; panic [label="Panic buying &\\nqueues at\\nneighbouring pumps"];
  fc [label="Forecast-driven\\nearly orders\\n(DryOut Shield)", fillcolor="#e3f4e8"];
  shock -> dep [label="+"]; dep -> indent [label="+"]; indent -> trucks [label="- (more demand\\nfor trucks)"];
  trucks -> lt [label="-"]; lt -> dry [label="+"]; dep -> dry [label="+"]; dry -> panic [label="+"];
  panic -> dep [label="+  R"]; fc -> dep [label="-  B"]; fc -> trucks [label="smooths\\nload"];
}""")
    st.caption("A demand shock depletes stock; simultaneous indents overload the fixed truck fleet, lead times grow, outlets "
               "dry out and customers queue at neighbouring pumps, depleting them too (reinforcing loop R). Ordering "
               "earlier, based on forecast cover and prioritised by risk, breaks the loop (balancing loop B).")
with t3:
    st.markdown("**Where DryOut Shield sits in the depot's daily decision process**")
    st.graphviz_chart("""
digraph {
  rankdir=LR; node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11];
  subgraph cluster_d { label="Data sources"; style=dashed; fontname="Helvetica";
    a [label="Outlet daily sales\\n& dip readings", fillcolor="#eef3fb"]; b [label="Outlet master\\n(tanks, distance)", fillcolor="#eef3fb"];
    c [label="PPAC market data", fillcolor="#eef3fb"]; }
  subgraph cluster_m { label="Analytics"; style=dashed; fontname="Helvetica";
    f [label="Demand forecast\\n(JMP ETS, 28 days)", fillcolor="#fff4dc"]; r [label="Replenishment rules\\nROP, quantity,\\ntruck priority", fillcolor="#fff4dc"]; }
  subgraph cluster_o { label="Decisions & outputs"; style=dashed; fontname="Helvetica";
    p [label="Dispatch plan\\n(CSV / PDF)", fillcolor="#e3f4e8"]; al [label="Dry-out alerts", fillcolor="#e3f4e8"];
    t [label="Transporter\\ntruck schedule", fillcolor="#e3f4e8"]; }
  a -> f; c -> f [style=dotted, label="trend &\\nseasonality"]; f -> r; b -> r; a -> r [label="current stock"];
  r -> p; r -> al; p -> t;
}""")
with t4:
    st.markdown("""
**Assumptions**
- One depot serving 30 outlets; depot stock is always sufficient (only trucks are limited).
- Truck = 20 kL in five 4 kL compartments; one trip serves one outlet-product order (multi-drop routing not modelled).
- Fuel ordered at the end of a day leaves the depot next morning and arrives after the outlet's transit time.
- Dead stock (unpumpable) = 5% of tank capacity. Orders never exceed the free space in the tank.
- Forecast uncertainty is taken from the JMP 95% forecast intervals; daily errors are treated as independent.
- Days on which an outlet ran dry are corrected before modelling (recorded sales understate demand).

**Limitations**
- **Outlet-level data is synthetic** (no OMC publishes outlet sales); it is calibrated to real PPAC monthly consumption
  (correlation 0.99 MS, 0.95 HSD) and real event dates. Real deployment needs OMC sales/automation data.
- No real-time tank automation feed; stock is entered or uploaded.
- Truck routing, driver hours and depot stock-outs are not modelled.
- Forecasts react to sudden shifts (e.g. price-gap demand) with a lag; use the Scenarios page to add a surge.
""")
with t5:
    st.markdown("""
| Technology | How it would extend DryOut Shield |
|---|---|
| **IoT automatic tank gauging** | Live stock and sales every 15 minutes replace manual dip readings; alerts fire in real time. |
| **AI / ML forecasting** | Gradient-boosting or deep models adding weather, price gaps, events and traffic as drivers. |
| **Agentic AI** | An agent raises indents and books trucks within approval limits, escalating exceptions to the manager. |
| **Digital twin** | A simulation twin of the depot–outlet network to stress-test strikes, floods or demand shocks before they happen. |
| **GPS / telematics** | Actual truck positions update arrival times and re-prioritise the plan during the day. |

**Risks and ethics.** Data privacy of dealer sales, dealer trust in automated orders, over-reliance on automation
during unusual events, and cybersecurity of connected tanks. Human approval should stay in the loop.
""")

with st.expander("Market context: real PPAC all-India consumption (Apr 2023 – Oct 2026)"):
    import plotly.express as px
    p = load_ppac()
    fig = px.line(p, x="month", y="consumption_tmt", color="product", markers=True,
                  labels={"consumption_tmt": "'000 tonnes", "month": ""},
                  color_discrete_map={"MS": "#2f6fdf", "HSD": "#d9822b"})
    fig.update_layout(height=320, margin=dict(t=10, b=10), legend_title=None)
    st.plotly_chart(fig, width="stretch")
    st.caption("Source: Petroleum Planning & Analysis Cell (PPAC), products-wise consumption. Diesel dips every monsoon "
               "(Jul–Sep) and peaks with harvest and festivals; both products grow 4–7% a year.")
