"""DryOut Shield - forecast-driven replenishment for fuel retail outlets.
SCA group project (GIM PGDM-BDA 2026-27, Term 5). Run:  streamlit run streamlit_app.py"""
import streamlit as st

st.set_page_config(page_title="DryOut Shield", page_icon="⛽", layout="wide")

from core.ui import sidebar  # noqa: E402  (after set_page_config)

pages = [
    st.Page("views/about.py", title="About & Context", icon=":material/info:", default=True),
    st.Page("views/data.py", title="Data", icon=":material/database:"),
    st.Page("views/forecast.py", title="Demand Forecast", icon=":material/insights:"),
    st.Page("views/planner.py", title="Replenishment Planner", icon=":material/local_shipping:"),
    st.Page("views/scenarios.py", title="Scenarios", icon=":material/tune:"),
    st.Page("views/insights.py", title="Insights & Export", icon=":material/summarize:"),
    st.Page("views/help.py", title="Help", icon=":material/help:"),
]
pg = st.navigation(pages)
st.sidebar.markdown("## ⛽ DryOut Shield")
st.sidebar.caption("Forecast-driven replenishment for fuel retail outlets")
sidebar()
pg.run()
