"""
Reusable UI Components for Streamlit App.
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict
from ..config import config, AnalysisMode

def render_sidebar():
    """Render the application sidebar."""
    with st.sidebar:
        st.title(f"🚀 {config.APP_NAME}")
        st.caption(f"v{config.APP_VERSION}")
        st.markdown("---")
        
        # Navigation
        st.markdown("### 🛠️ Navigation Mode")
        mode = st.radio(
            "Choose Analysis Type", 
            [m.value for m in AnalysisMode],
            key="app_mode_selection"
        )
        
        
        # Update session state
        st.session_state.app_mode = mode
        
        st.markdown("---")
        st.markdown("### ⚙️ Settings")
        
        # Model Selection (Placeholder for future llm config)
        st.selectbox("AI Model", ["Hybrid (Local + Cloud)", "Cloud Only (Fast)", "Local Only (Secure)"], index=0)
        
        st.markdown("---")
        with st.expander("ℹ️ About"):
            st.info(
                "Financial Alpha Intelligence is an advanced AI agent demonstrating "
                "financial modeling capabilities."
            )

def render_export_utility(
    tab_name: str, 
    title: str, 
    subtitle: str, 
    metrics: Dict = None,
    data_frames: Dict[str, pd.DataFrame] = None
):
    """
    Render a standardized export section at the bottom of tabs.
    Allows downloading data as CSV/Excel.
    """
    st.markdown("---")
    st.subheader(f"📥 Export {title} Data")
    st.markdown(subtitle)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if data_frames:
            for name, df in data_frames.items():
                csv = df.to_csv(index=True).encode('utf-8')
                st.download_button(
                    label=f"Download {name} (CSV)",
                    data=csv,
                    file_name=f"{name.lower().replace(' ', '_')}.csv",
                    mime="text/csv",
                    key=f"dl_{tab_name}_{name}"
                )
    
    with col2:
        st.info("💡 Pro Tip: You can also generate a full PDF report in the 'Report Generation' tab.")

def apply_custom_css():
    """Apply custom CSS styles to the application (Premium Dark Theme)."""
    st.markdown("""
        <style>
            /* Main App Background - Let Streamlit handled dark mode, but enhance contrast */
            .stApp {
                /* background-color: #0f172a; Removed to respect user preference, but we style components for dark mode */
            }
            
            /* Buttons */
            .stButton>button {
                width: 100%;
                border-radius: 8px;
                height: 3em;
                background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
                color: white;
                font-weight: 600;
                border: none;
                transition: all 0.3s ease;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            }
            .stButton>button:hover {
                background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
                transform: translateY(-2px);
                box-shadow: 0 6px 12px rgba(37, 99, 235, 0.4);
            }
            
            /* Metric Cards & Containers (Glassmorphism) */
            .metric-card, div[data-testid="stMetric"], div[data-testid="metric-container"] {
                background-color: rgba(30, 41, 59, 0.4);
                padding: 1rem;
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.1);
                backdrop-filter: blur(10px);
            }
            
            /* Typography */
            h1, h2, h3 {
                color: #e2e8f0 !important;
                font-family: 'Inter', sans-serif;
                font-weight: 700;
            }
            p, label, .stMarkdown {
                color: #cbd5e1;
            }
            
            /* Tabs Styling - CRITICAL FIX */
            .stTabs [data-baseweb="tab-list"] {
                gap: 10px;
                background-color: transparent;
                padding-bottom: 10px;
            }
            
            .stTabs [data-baseweb="tab"] {
                height: 45px;
                white-space: pre-wrap;
                background-color: rgba(30, 41, 59, 0.5); /* Semi-transparent dark */
                color: #94a3b8; /* Dimmed text */
                border-radius: 8px;
                border: 1px solid rgba(148, 163, 184, 0.1);
                padding: 0 20px;
                transition: all 0.2s;
            }
            
            .stTabs [aria-selected="true"] {
                background-color: #1e3a8a !important; /* Active Tab Background */
                color: #60a5fa !important; /* Active Tab Text */
                border: 1px solid #3b82f6 !important;
            }
            
            /* File Uploader */
            section[data-testid="stFileUploader"] {
                background-color: rgba(30, 41, 59, 0.3);
                border-radius: 12px;
                padding: 20px;
                border: 1px dashed #475569;
            }
            
            /* Charts */
            .js-plotly-plot .plotly .modebar {
                background: transparent !important;
            }
        </style>
    """, unsafe_allow_html=True)
