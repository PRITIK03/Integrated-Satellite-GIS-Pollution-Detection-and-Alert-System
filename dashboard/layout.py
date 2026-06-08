"""
Dashboard layout and page setup.
"""

import streamlit as st


def configure_page():
    st.set_page_config(
        page_title="Pollution Detection System",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def apply_styles():
    st.markdown(
        """
        <style>
            .main-header {
                font-size: 3rem;
                color: #1f77b4;
                text-align: center;
                margin-bottom: 2rem;
                font-weight: bold;
            }
            .metric-card {
                background-color: #f0f2f6;
                padding: 1rem;
                border-radius: 0.5rem;
                border-left: 4px solid #1f77b4;
            }
            .risk-good { color: #28a745; }
            .risk-moderate { color: #ffc107; }
            .risk-unhealthy { color: #fd7e14; }
            .risk-hazardous { color: #dc3545; }
            .sidebar .sidebar-content {
                background-color: #f8f9fa;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(dashboard):
    dashboard.main_header()
