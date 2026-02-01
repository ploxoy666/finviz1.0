"""
Deep Report Analyzer UI Module.
Handles the main workflow: PDF Upload -> Extraction -> Analysis -> Reporting.
"""

import streamlit as st
import pandas as pd
import os
import tempfile
from pathlib import Path
from loguru import logger
import plotly.graph_objects as go
import plotly.express as px

from ..config import config, ScenarioType
from ..core.pdf_parser import PDFParser
from ..core.financial_extractor import FinancialExtractor
from ..core.model_engine import ModelEngine
from ..core.forecast_engine import ForecastEngine
from ..core.report_generator import ReportGenerator
from ..models.schemas import ForecastAssumptions

# Optional AI components
try:
    from ..core.summarizer import FinancialSummarizer
    from ..core.sentiment_analyzer import SentimentAnalyzer
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

from .components import render_export_utility

def render_report_analyzer():
    """Render the main Deep Report Intelligence interface."""
    st.markdown("## 📄 Deep Report Intelligence")
    st.caption("Engine Version: v3.3 | Multi-Scale Core | Fixed Type Safety in Re-scaling")
    st.info("Upload 10-K/10-Q PDF files for full automated analysis, 3-statement modeling, and valuation.")
    
    # File Uploader
    uploaded_file = st.file_uploader("Upload Financial Report (PDF)", type="pdf")
    
    if uploaded_file:
        _process_file_upload(uploaded_file)
    
    # Display Results if analysis is complete
    if st.session_state.get("analysis_complete") and "model" in st.session_state:
        model = st.session_state.model
        
        # Tabs for result visualization
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Executive Dashboard", 
            "📈 Financials & Forecast", 
            "💎 Valuation (DCF)", 
            "🧠 AI Risk & Sentiment",
            "📥 Report Generation"
        ])
        
        # Data Adjustment Sidebar
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 🛠️ Data Adjustments")
            
            # Scale Selector
            scale_options = {
                "Actuals": 1.0,
                "Thousands (x1k)": 1000.0,
                "Millions (x1MM)": 1000000.0,
                "Billions (x1B)": 1000000000.0
            }
            current_scale_key = st.session_state.get("current_scale", "Actuals")
            selected_scale = st.selectbox(
                "Report Units (Source)", 
                list(scale_options.keys()), 
                index=list(scale_options.keys()).index(current_scale_key) if current_scale_key in scale_options else 0,
                help="If the report lists figures as '137' for $137M, select 'Millions'."
            )
            
            if selected_scale != current_scale_key:
                _apply_scale_and_rebuild(selected_scale, scale_options[selected_scale])

        with tab1:
            _render_dashboard(model)
            
        with tab2:
            _render_financials(model)
            
        with tab3:
            _render_valuation(model)
            
        with tab4:
             _render_ai_analysis(model)
             
        with tab5:
            _render_report_generation(model)


def _process_file_upload(uploaded_file):
    """Handle file processing workflow."""
    if st.button("🚀 Analyze Report"):
        with st.status("Running Financial Alpha Intelligence...", expanded=True) as status:
            try:
                # 1. Save temp file
                status.write("📂 Reading PDF file...")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                # 2. Parse PDF
                status.write("🔍 Extracting text and tables (OCR)...")
                parser = PDFParser(tmp_path)
                data = parser.extract()
                
                # 3. Extract Financials
                status.write("🔢 Identifying financial statements...")
                pages_dict = {i: p for i, p in enumerate(data['pages'])}
                extractor = FinancialExtractor(pages_dict)
                
                # IMPORTANT: Store TRULY RAW statements (unscaled) for accurate re-scaling later
                st.session_state.raw_statements = extractor.extract(apply_scale=False)
                
                # Detect the INITIAL scale to use it for the first build
                detected_scale = extractor.scale_factor
                scale_name_map = {1.0: "Actuals", 1000.0: "Thousands (x1k)", 1000000.0: "Millions (x1MM)", 1000000000.0: "Billions (x1B)"}
                initial_scale_name = scale_name_map.get(detected_scale, "Actuals")
                
                # 4. Create Initial Model using detected scale
                # We reuse the logic from _apply_scale_and_rebuild but inline for the first run
                import copy
                raw_data = copy.deepcopy(st.session_state.raw_statements)
                
                # Scale it
                skip_fields = {'period_end', 'period_start', 'fiscal_year'}
                for category in ['income_statements', 'balance_sheets', 'cash_flow_statements']:
                    stmts = getattr(raw_data, category, [])
                    for stmt in stmts:
                        # Cross-version Pydantic field access
                        fields = getattr(stmt, '__fields__', None) or getattr(stmt, 'model_fields', {})
                        for field in fields:
                            if field not in skip_fields:
                                val = getattr(stmt, field)
                                if isinstance(val, (int, float)) and val is not None:
                                    setattr(stmt, field, val * detected_scale)
                
                model_engine = ModelEngine(raw_data)
                linked_model = model_engine.build_linked_model()
                
                # 5. Forecast & Valuation
                status.write("🔮 Generating Forecasts & DCF Valuation...")
                fc_engine = ForecastEngine(linked_model)
                final_model = fc_engine.forecast(years=5, scenario=ScenarioType.BASE)
                final_model = fc_engine.generate_investment_advice()
                
                # Store results
                st.session_state.model = final_model
                st.session_state.current_scale = initial_scale_name
                st.session_state.analysis_complete = True
                
                # 6. AI Analysis (Async-like) - Wrap in try/except to prevent crash
                if AI_AVAILABLE:
                    try:
                        status.write("🧠 Running AI Sentiment & Risk Analysis...")
                        summarizer = FinancialSummarizer(api_key=config.api.HF_API_KEY)
                        sentiment = SentimentAnalyzer(api_key=config.api.HF_API_KEY)
                        
                        full_text = data['text']
                        st.session_state.ai_summary = summarizer.summarize(full_text)
                        st.session_state.ai_risks = summarizer.extract_risks(full_text)
                        st.session_state.ai_sentiment = sentiment.analyze_report(data['pages'])
                    except Exception as ai_err:
                        logger.error(f"AI Analysis failed: {ai_err}")
                        st.session_state.ai_summary = "AI Summary temporarily unavailable."
                        st.session_state.ai_risks = ["Analysis bypassed."]
                
                # Store results
                st.session_state.model = final_model
                st.session_state.analysis_complete = True
                
                # Cleanup
                os.unlink(tmp_path)
                status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
                st.rerun()
                
            except Exception as e:
                status.update(label="❌ Error Occurred", state="error")
                st.error(f"An error occurred: {str(e)}")
                logger.error(f"Processing error: {e}")

def _render_dashboard(model):
    """Render Executive Dashboard tab."""
    st.subheader(f"Executive Summary: {model.company_name}")
    
    # Styled AI Summary (Moved to top for visibility)
    st.markdown(f"""
    <div style="
        padding: 20px; 
        background-color: rgba(15, 23, 42, 1); 
        border: 2px solid #334155; 
        border-radius: 12px; 
        margin-bottom: 25px;
        color: #f8fafc;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 10px; margin-bottom: 15px;">
            <h3 style="margin: 0; color: #60a5fa; font-size: 1.4em;">🧠 Alpha Investment Thesis</h3>
            <span style="
                padding: 6px 16px; 
                background-color: {'#16a34a' if model.recommendation == 'BUY' else '#ca8a04' if model.recommendation == 'HOLD' else '#dc2626'}; 
                border-radius: 30px; 
                font-weight: 800;
                font-size: 0.85em;
                letter-spacing: 0.05em;
                color: white;
            ">
                {model.recommendation or 'NEUTRAL'}
            </span>
        </div>
        <div style="font-size: 1.1em; line-height: 1.6;">
            <p style="margin-bottom: 10px;"><strong>Thesis:</strong> {model.investment_thesis or st.session_state.ai_summary or 'No analysis available.'}</p>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <div><strong>Target Price:</strong> <span style="color: #4ade80; font-weight: bold;">{f'${model.target_price:,.2f}' if model.target_price else 'N/A'}</span></div>
                <div><strong>Upside:</strong> <span style="color: {'#4ade80' if (model.upside_potential or 0) > 0 else '#fb7185'}; font-weight: bold;">{f'{model.upside_potential:+.1%}' if model.upside_potential else 'N/A'}</span></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    # Key Metrics
    latest_inc = model.historical_income_statements[-1]
    forecast_inc = model.forecast_income_statements[0]
    
    # Metrics Calculation
    rev_growth = 0.0
    if len(model.historical_income_statements) > 1:
        prev_rev = model.historical_income_statements[-2].revenue
        if prev_rev and prev_rev > 0:
            rev_growth = (latest_inc.revenue - prev_rev) / prev_rev

    # Calculate margins safely
    gross_margin = (latest_inc.gross_profit / latest_inc.revenue) if latest_inc.revenue else 0.0
    op_margin = (latest_inc.operating_income / latest_inc.revenue) if latest_inc.revenue else 0.0
    net_margin = (latest_inc.net_income / latest_inc.revenue) if latest_inc.revenue else 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Revenue (TTM)", _format_metric(latest_inc.revenue), f"{rev_growth:+.1%}")
    m2.metric("Gross Margin", f"{gross_margin:.1%}")
    m3.metric("Operating Margin", f"{op_margin:.1%}")
    m4.metric("Net Margin", f"{net_margin:.1%}")
    
    # Scale Warning
    if latest_inc.revenue < 100000 and st.session_state.get('current_scale') == 'Actuals':
        st.warning(f"⚠️ **Scale Alert:** Revenue is only {_format_metric(latest_inc.revenue)}. Many reports use Millions/Billions. If this looks too low, use the sidebar to change 'Data Scale' to Millions.")
        if st.button("🚀 Quick Fix: Switch to Millions"):
            _apply_scale_and_rebuild("Millions (x1MM)", 1000000.0)
    
    st.markdown("---")
    
    # Charts Section
    st.subheader("Financial Trends")
    import plotly.graph_objects as go
    import pandas as pd
    
    if len(model.historical_income_statements) > 0:
        hist_data = {
            "Year": [s.period_end.year for s in model.historical_income_statements],
            "Revenue": [s.revenue for s in model.historical_income_statements],
            "Net Income": [s.net_income for s in model.historical_income_statements],
            "Operating Income": [s.operating_income for s in model.historical_income_statements]
        }
        df_chart = pd.DataFrame(hist_data)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_chart['Year'], 
            y=df_chart['Revenue'], 
            name='Revenue',
            marker_color='#3b82f6'
        ))
        fig.add_trace(go.Scatter(
            x=df_chart['Year'], 
            y=df_chart['Net Income'], 
            name='Net Income',
            mode='lines+markers',
            line=dict(color='#22c55e', width=3)
        ))
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient historical data for visualization.")

    
def _format_metric(value):
    """Format numbers into human-readable strings with Million/Billion suffixes."""
    if value is None:
        return "N/A"
    
    abs_val = abs(value)
    if abs_val == 0:
        return "$0"
    
    # Thresholds for suffixes
    if abs_val >= 1_000_000_000:
        return f"${value/1_000_000_000:,.2f}B"
    elif abs_val >= 1_000_000:
        return f"${value/1_000_000:,.1f}M"
    elif abs_val >= 1_000:
        return f"${value/1_000:,.0f}K"
    elif abs_val >= 10:
        return f"${value:,.0f}"
    else:
        return f"${value:,.2f}"

def _render_financials(model):
    """Render Financials tab with forecast controls."""
    st.subheader("Financial Forecast")
    
    # Scenario Controls
    col_s1, col_s2 = st.columns(2)
    current_scenario = model.assumptions.scenario if model.assumptions and model.assumptions.scenario else ScenarioType.BASE
    scenario_list = [s.value for s in ScenarioType]
    scenario = col_s1.selectbox(
        "Growth Scenario", 
        scenario_list, 
        index=scenario_list.index(current_scenario) if current_scenario in scenario_list else 0
    )
    
    if st.button("Update Forecast"):
        fc_engine = ForecastEngine(model)
        new_model = fc_engine.forecast(years=5, scenario=scenario)
        new_model = fc_engine.generate_investment_advice()
        st.session_state.model = new_model
        st.rerun()
    
    # Display Forecast Table
    rows = []
    
    # Initial previous revenue for growth calc
    prev_revenue = model.historical_income_statements[-1].revenue if model.historical_income_statements else 0
    
    for inc in model.forecast_income_statements:
        # Calculate growth
        growth = 0.0
        if prev_revenue and prev_revenue > 0:
            growth = (inc.revenue - prev_revenue) / prev_revenue
        prev_revenue = inc.revenue
        
        rows.append({
            "Year": inc.period_end.year,
            "Revenue": _format_metric(inc.revenue),
            "Growth": f"{growth:.1%}",
            "Net Income": _format_metric(inc.net_income)
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

def _render_valuation(model):
    """Render Valuation tab."""
    dcf = model.dcf_valuation
    st.subheader("Discounted Cash Flow (DCF)")
    
    c1, c2 = st.columns(2)
    # Safe rendering for assumptions
    wacc = model.assumptions.wacc if model.assumptions and model.assumptions.wacc is not None else 0.0
    term_growth = model.assumptions.terminal_growth_rate if model.assumptions and model.assumptions.terminal_growth_rate is not None else 0.0
    
    c1.metric("WACC", f"{wacc:.1%}")
    c1.metric("Terminal Growth", f"{term_growth:.1%}")
    
    # Intreactive WACC Adjustment
    with st.expander("⚙️ Adjust Valuation Assumptions", expanded=True):
        new_wacc = st.slider("WACC (%)", 0.0, 20.0, float(wacc * 100), 0.1) / 100.0
        new_tg = st.slider("Terminal Growth (%)", 0.0, 5.0, float(term_growth * 100), 0.1) / 100.0
        
        if new_wacc != wacc or new_tg != term_growth:
            if st.button("Recalculate DCF"):
                # Update assumptions and re-run forecast
                model.assumptions.wacc = new_wacc
                model.assumptions.terminal_growth_rate = new_tg
                # Re-run forecast engine to update DCF
                fc = ForecastEngine(model)
                # FIX: Use keyword arguments to avoid positional mismatch
                new_model = fc.forecast(years=model.forecast_years, scenario=model.assumptions.scenario or ScenarioType.BASE)
                new_model = fc.generate_investment_advice()
                st.session_state.model = new_model
                st.rerun()

    if dcf and dcf.enterprise_value > 0:
        c2.metric("Enterprise Value", _format_metric(dcf.enterprise_value))
        c2.metric("Equity Value", _format_metric(dcf.equity_value))
        st.metric("Implied Price per Share", f"${dcf.implied_price_per_share:,.2f}")
    else:
        if wacc == 0:
            st.warning("⚠️ WACC is 0%. Please adjust WACC above to generate DCF.")
        else:
            st.warning("DCF Valuation could not be computed (Negative Cash Flows or NaN).")

def _render_ai_analysis(model):
    """Render AI Analysis tab."""
    st.subheader("🧠 Sentiment & Risk Analysis")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Key Risks")
        if st.session_state.get("ai_risks"):
            for risk in st.session_state.ai_risks:
                st.warning(f"• {risk}")
        else:
            st.info("AI analysis not available.")
            
    with c2:
        st.markdown("### Sentiment Analysis")
        sent = st.session_state.get("ai_sentiment")
        if sent:
            st.metric("Dominant Sentiment", sent['dominant_sentiment'].upper())
            st.progress(sent['breakdown'].get('positive', 0))
            st.caption(f"Positive Score: {sent['breakdown'].get('positive', 0):.0%}")

def _render_report_generation(model):
    """Render Report Generation tab."""
    st.subheader("📄 Generate PDF Report")
    
    if st.button("Generate Comprehensive Investment Memo"):
        with st.spinner("Generating PDF..."):
            import io
            pdf_buffer = io.BytesIO()
            
            generator = ReportGenerator(model)
            generator.generate_pdf(pdf_buffer)
            pdf_data = pdf_buffer.getvalue()
            
            st.success("Report Generated!")
            st.download_button(
                label="📥 Download Investment Memo (PDF)",
                data=pdf_data,
                file_name=f"{model.ticker}_Investment_Memo.pdf",
                mime="application/pdf"
            )

def _apply_scale_and_rebuild(scale_name, scale_factor):
    """Rebuild model with scaled data."""
    import copy
    
    # Avoid infinite reruns if scale is same
    if st.session_state.get("current_scale") == scale_name:
        return

    with st.spinner(f"Rescaling data to {scale_name}..."):
        if "raw_statements" not in st.session_state:
            st.error("Raw data missing. Please upload a report first.")
            return

        # 1. Start from TRULY RAW statements
        raw_base = copy.deepcopy(st.session_state.raw_statements)
        
        # 2. Apply the scale factor to the raw base
        skip_fields = {'period_end', 'period_start', 'fiscal_year'}
        
        for category in ['income_statements', 'balance_sheets', 'cash_flow_statements']:
            if hasattr(raw_base, category):
                stmts = getattr(raw_base, category)
                for stmt in stmts:
                    # Support for both Pydantic v1 and v2
                    fields = getattr(stmt, '__fields__', None) or getattr(stmt, 'model_fields', {})
                    for field in fields:
                        if field not in skip_fields:
                            val = getattr(stmt, field)
                            if isinstance(val, (int, float)) and val is not None:
                                # Special handling for shares to avoid double scaling
                                if 'shares' in field.lower() and val > 500_000:
                                    continue
                                setattr(stmt, field, val * scale_factor)
        
        # 3. Rebuild (Full cycle: Link -> Forecast -> Advice/DCF)
        try:
            model_engine = ModelEngine(raw_base)
            linked_model = model_engine.build_linked_model()
            
            fc_engine = ForecastEngine(linked_model)
            current_scenario = ScenarioType.BASE
            if "model" in st.session_state and hasattr(st.session_state.model, 'assumptions') and st.session_state.model.assumptions:
                 if st.session_state.model.assumptions.scenario:
                     current_scenario = st.session_state.model.assumptions.scenario

            # Re-run forecast
            final_model = fc_engine.forecast(years=5, scenario=current_scenario)
            # Re-calculate DCF & Advice
            final_model = fc_engine.generate_investment_advice()
            
            st.session_state.model = final_model
            st.session_state.current_scale = scale_name
            st.success(f"Successfully rescaled to {scale_name}. DCF updated with full values.")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error rescaling model: {e}")
