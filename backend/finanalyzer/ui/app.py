"""
Main UI Entry Point.
Orchestrates the application modes and layout.
"""

import streamlit as st
from .components import render_sidebar, apply_custom_css
from .market_pulse import render_market_pulse
from .report_analyzer import render_report_analyzer
from .startup_valuator import render_startup_valuator
from ..config import config, AnalysisMode

def main():
    """Main application loop."""
    # 1. Page Config
    st.set_page_config(
        page_title=config.APP_NAME,
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 2. Apply Styles
    apply_custom_css()
    
    # 3. Session State Initialization
    if "app_mode" not in st.session_state:
        st.session_state.app_mode = AnalysisMode.QUICK_PULSE
    if "analysis_complete" not in st.session_state:
        st.session_state.analysis_complete = False
    if "model" not in st.session_state:
        st.session_state.model = None
    if "report_path" not in st.session_state:
        st.session_state.report_path = None
    if "market_data" not in st.session_state:
        st.session_state.market_data = None
    
    # AI States
    if "ai_summary" not in st.session_state:
        st.session_state.ai_summary = None
    if "ai_risks" not in st.session_state:
        st.session_state.ai_risks = []
    if "ai_sentiment" not in st.session_state:
        st.session_state.ai_sentiment = None
    
    # 3. Sidebar Navigation
    render_sidebar()
    
    # 4. Route to Mode
    mode = st.session_state.get("app_mode", AnalysisMode.QUICK_PULSE)
    
    if mode == AnalysisMode.QUICK_PULSE:
        render_market_pulse()
        
    elif mode == AnalysisMode.DEEP_REPORT:
        render_report_analyzer()
        
    elif mode == AnalysisMode.STARTUP_VALUATOR:
        render_startup_valuator()
    
    else:
        st.error("Unknown application mode selected.")

if __name__ == "__main__":
    main()
