"""Shared UI pieces: sidebar settings, status colours, KPI row."""
import streamlit as st

from core.data import get_ds

STATUS_COLORS = {"Red": "#d64545", "Amber": "#e0a100", "Green": "#2e9d5b"}
PRODUCT_COLORS = {"MS": "#2f6fdf", "HSD": "#d9822b"}


def sidebar():
    ds = get_ds()
    with st.sidebar:
        st.markdown("### Planning settings")
        st.select_slider("Target service level", options=[0.90, 0.95, 0.98, 0.99, 0.995],
                         key="service_level", format_func=lambda v: f"{v:.1%}",
                         help="Probability that an outlet does NOT run dry before its next delivery. "
                              "Higher = more safety stock and earlier orders.")
        st.number_input("Depot truck trips per day (K)", min_value=5, max_value=100, step=1, key="trucks_per_day",
                        help="Tank-truck trips (20 kL each) the depot can send per day.")
        st.divider()
        st.caption(f"**Data:** {ds['source']}")
        st.caption(f"**Stock as of:** {ds['as_of']:%d %b %Y} · **Forecasts:** {ds['forecast_engine']}")


def status_badge(s: str) -> str:
    return f":{'red' if s == 'Red' else 'orange' if s == 'Amber' else 'green'}[● {s}]"


def style_status(df, col="status"):
    def f(v):
        c = STATUS_COLORS.get(v)
        return f"background-color: {c}; color: white; font-weight: 600" if c else ""
    return df.style.map(f, subset=[col])
