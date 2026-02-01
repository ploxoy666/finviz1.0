"""
Startup Valuator UI Module.
Handles manual driver input and Excel upload for private company valuation.
"""

import streamlit as st
from datetime import date
import pandas as pd
import os
from typing import Dict, List, Optional
import re

from ..config import config, DefaultMetrics
from ..models.schemas import (
    ForecastAssumptions, 
    FinancialStatements, 
    IncomeStatement, 
    BalanceSheet, 
    CashFlowStatement,
    ReportType,
    AccountingStandard,
    Currency
)
from ..core.model_engine import ModelEngine
from ..core.forecast_engine import ForecastEngine
from ..core.report_generator import ReportGenerator
from .components import render_export_utility

def render_startup_valuator():
    """Render the private/startup valuation interface."""
    st.markdown("## 🦄 Startup & Private Company Valuation")
    st.info("Build professional 3-Statement Models and DCF Valuations from manual drivers - perfect for pre-IPO companies.")

    p_tab1, p_tab2 = st.tabs(["✍️ Driver Inputs", "📂 Excel Upload (Beta)"])

    with p_tab1:
        _render_manual_input()

    with p_tab2:
        _render_excel_upload()

    # Display Results if model exists and is in startup mode
    if st.session_state.get("startup_mode") and "model" in st.session_state:
        _render_valuation_results(st.session_state.model)

def _render_manual_input():
    with st.form("startup_drivers"):
        st.markdown("### 1. Company Profile")
        col_a, col_b = st.columns(2)
        p_company = col_a.text_input("Company Name", "My Startup Inc.")
        p_currency = col_b.selectbox("Currency", [c.value for c in Currency], index=0)
        
        st.markdown("### 2. Current Year Financials (Base Year)")
        c1, c2, c3 = st.columns(3)
        p_rev = c1.number_input("Revenue ($)", min_value=0.0, value=1_000_000.0, step=1000.0)
        p_ni = c2.number_input("Net Income ($)", value=100_000.0, step=1000.0)
        p_cash = c3.number_input("Cash on Hand ($)", min_value=0.0, value=500_000.0, step=1000.0)
        
        p_shares = st.number_input("Shares Outstanding", min_value=1, value=1_000_000, step=100)
        
        st.markdown("### 3. Forecast Assumptions")
        a1, a2, a3 = st.columns(3)
        a_growth = a1.slider("Annual Revenue Growth", 0.0, 2.0, config.defaults.REVENUE_GROWTH_RATE)
        a_margin = a2.slider("Target Operating Margin", -0.5, 0.8, config.defaults.OPERATING_MARGIN)
        a_tax = a3.slider("Tax Rate", 0.0, 0.40, config.defaults.TAX_RATE)
        
        st.markdown("### 4. Valuation Drivers")
        v1, v2 = st.columns(2)
        a_wacc = v1.slider("WACC (Discount Rate)", 0.05, 0.25, 0.12)
        a_term = v2.slider("Terminal Growth", 0.01, 0.06, config.defaults.TERMINAL_GROWTH_RATE)
        
        submit_startup = st.form_submit_button("🔨 Build Model & Value")
        
    if submit_startup:
        with st.spinner("Synthesizing financial model from drivers..."):
            # 1. Create Base Year Data (Synthetic)
            curr_date = date.today()
            
            # Simplified Income Statement
            base_inc = IncomeStatement(
                period_start=date(curr_date.year-1, 1, 1),
                period_end=date(curr_date.year-1, 12, 31),
                currency=p_currency,
                revenue=p_rev,
                cost_of_revenue=p_rev * 0.4, # Assumption
                gross_profit=p_rev * 0.6,
                operating_expenses=p_rev * 0.6 - (p_rev * a_margin), # Backsolve
                operating_income=p_rev * a_margin,
                net_income=p_ni,
                shares_outstanding_basic=p_shares,
                shares_outstanding_diluted=p_shares
            )
            
            # Simplified Balance Sheet
            base_bs = BalanceSheet(
                period_end=date(curr_date.year-1, 12, 31),
                currency=p_currency,
                total_assets=p_cash + (p_rev * 0.2), # Approx
                total_liabilities=(p_rev * 0.1),
                total_shareholders_equity=(p_cash + (p_rev * 0.2)) - (p_rev * 0.1),
                cash_and_equivalents=p_cash,
                total_current_assets=p_cash,
                retained_earnings=p_ni,
                common_stock=p_shares
            )
            
            # Simplified Cash Flow
            base_cf = CashFlowStatement(
                period_start=date(curr_date.year-1, 1, 1),
                period_end=date(curr_date.year-1, 12, 31),
                currency=p_currency,
                net_income=p_ni,
                cash_from_operations=p_ni, # simplified
                net_change_in_cash=0,
                cash_beginning_of_period=p_cash,
                cash_end_of_period=p_cash
            )
            
            stmts = FinancialStatements(
                company_name=p_company,
                fiscal_year=curr_date.year-1,
                report_type=ReportType.ANNUAL_REPORT,
                currency=p_currency,
                accounting_standard=AccountingStandard.GAAP,
                income_statements=[base_inc],
                balance_sheets=[base_bs],
                cash_flow_statements=[base_cf]
            )
            
            _build_and_store_model(stmts, a_growth, a_margin, a_tax, a_wacc, a_term)

def _render_excel_upload():
    st.markdown("### 📂 Upload Historical Financials")
    st.markdown("Upload a CSV/Excel with columns: `Year`, `Revenue`, `Net_Income`, `Cash`, `Debt`.")
    
    uploaded_excel = st.file_uploader("Upload CSV or Excel", type=['csv', 'xlsx'])
    
    if uploaded_excel:
        try:
            # Smart Load
            if uploaded_excel.name.endswith('.csv'):
                df = pd.read_csv(uploaded_excel)
            else:
                df = pd.read_excel(uploaded_excel)
                
            # Normalize Headers
            df.columns = [c.strip().replace(' ', '_') for c in df.columns]
            st.dataframe(df.head())
            
            with st.form("excel_review"):
                st.subheader("📝 Review & Generate Model")
                
                edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
                
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    e_growth = st.slider("Forecast Revenue Growth (%)", -20, 200, 25) / 100
                    e_target_val = st.number_input("Target Valuation ($)", value=10_000_000.0)
                with col_e2:
                    e_wacc = st.slider("WACC / Discount Rate (%)", 5, 30, 12) / 100
                    e_target_irr = st.slider("Target IRR (%)", 10, 50, 25) / 100
                    
                submit_excel = st.form_submit_button("🚀 Generate Model from Excel")
                
            if submit_excel:
                # Convert DF to Statements
                inc_stmts = []
                bal_sheets = []
                cf_stmts = []
                
                edited_df = edited_df.sort_values(by=edited_df.columns[0]) # Assume Year is first
                
                for _, row in edited_df.iterrows():
                    # Flexible mapping
                    year = int(row.get('Year', row.get('Date', 2023)))
                    rev = float(row.get('Revenue', 0))
                    ni = float(row.get('Net_Income', row.get('Profit', 0)))
                    cash = float(row.get('Cash', row.get('Cash_Balance', 0)))
                    debt = float(row.get('Debt', row.get('Total_Debt', 0)))
                    assets = float(row.get('Total_Assets', row.get('Assets', cash + rev * 0.5)))
                    
                    # IS
                    inc_stmts.append(IncomeStatement(
                        period_start=date(year, 1, 1),
                        period_end=date(year, 12, 31),
                        revenue=rev,
                        net_income=ni,
                        gross_profit=rev * 0.6, # Default
                        operating_income=ni * 1.2 # Default
                    ))
                    
                    # BS
                    bal_sheets.append(BalanceSheet(
                        period_end=date(year, 12, 31),
                        total_assets=assets,
                        cash_and_equivalents=cash,
                        total_liabilities=debt,
                        total_shareholders_equity=assets - debt
                    ))
                    
                    # CF
                    cf_stmts.append(CashFlowStatement(
                        period_start=date(year, 1, 1),
                        period_end=date(year, 12, 31),
                        net_income=ni,
                        cash_from_operations=ni,
                        cash_end_of_period=cash
                    ))

                company_name = os.path.splitext(uploaded_excel.name)[0]
                stmts = FinancialStatements(
                    company_name=company_name,
                    fiscal_year=inc_stmts[-1].period_end.year,
                    report_type=ReportType.ANNUAL_REPORT,
                    accounting_standard=AccountingStandard.GAAP,
                    income_statements=inc_stmts,
                    balance_sheets=bal_sheets,
                    cash_flow_statements=cf_stmts
                )
                
                _build_and_store_model(stmts, e_growth, 0.2, 0.21, e_wacc, 0.02)
                
        except Exception as e:
            st.error(f"Error processing file: {e}")

def _build_and_store_model(stmts, growth, margin, tax, wacc, term):
    # Initialize Engines
    model_engine = ModelEngine(stmts)
    linked_model = model_engine.build_linked_model()
    
    assumptions = ForecastAssumptions(
        revenue_growth_rate=growth,
        gross_margin=0.6, # Simplified
        operating_margin=margin,
        tax_rate=tax,
        wacc=wacc,
        terminal_growth_rate=term,
        capex_percent_of_revenue=0.05
    )
    
    fc_engine = ForecastEngine(linked_model)
    final_model = fc_engine.forecast(years=5, assumptions=assumptions)
    
    # Store in session
    st.session_state.model = final_model
    st.session_state.startup_mode = True
    
    # Generate PDF
    generator = ReportGenerator(final_model, sentiment_data=None)
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    report_name = f"Startup_Valuation_{stmts.company_name}.pdf"
    report_path = os.path.join(output_dir, report_name)
    generator.generate_pdf(report_path)
    st.session_state.report_path = report_path
    
    st.success("Valuation Model Built Successfully!")
    st.rerun()

def _render_valuation_results(model):
    """Render valuation results with proper styling."""
    dcf = model.dcf_valuation
    
    st.markdown("---")
    st.subheader(f"🦄 Valuation Results: {model.company_name}")
    
    # Styled Metrics Container
    st.markdown("""
    <style>
        .val-metric {
            background-color: rgba(30, 41, 59, 0.5);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #475569;
            text-align: center;
        }
        .val-metric h2 {
            margin: 0;
            color: #38bdf8;
        }
        .val-metric p {
            margin: 0;
            color: #94a3b8;
            font-size: 0.9em;
        }
    </style>
    """, unsafe_allow_html=True)
    
    m1, m2, m3 = st.columns(3)
    
    if dcf:
        with m1:
            st.markdown(f'<div class="val-metric"><h2>${dcf.enterprise_value/1e6:,.1f}M</h2><p>Enterprise Value</p></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="val-metric"><h2>${dcf.equity_value/1e6:,.1f}M</h2><p>Equity Value</p></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="val-metric"><h2>${dcf.implied_price_per_share:,.2f}</h2><p>Implied Share Price</p></div>', unsafe_allow_html=True)
        
        st.write("") # Spacer
        
        # Show DCF Table within an expander that is OPEN by default
        with st.expander("💸 Discounted Cash Flow Forecast", expanded=True):
            # Construct DataFrame for display
            rows = []
            for year_data in dcf.forecast_period_fcf:
                rows.append({
                    "Year": year_data.year,
                    "Revenue ($)": year_data.revenue,
                    "EBIT ($)": year_data.ebit,
                    "Free Cash Flow ($)": year_data.free_cash_flow,
                    "PV of FCF ($)": year_data.pv_free_cash_flow
                })
                
            df_dcf = pd.DataFrame(rows)
            # Format large numbers
            st.dataframe(
                df_dcf.style.format({
                    "Revenue ($)": "${:,.0f}", 
                    "EBIT ($)": "${:,.0f}",
                    "Free Cash Flow ($)": "${:,.0f}",
                    "PV of FCF ($)": "${:,.0f}"
                }), 
                use_container_width=True
            )
        
        render_export_utility("startup", "Valuation Model", "Download the full DCF model.", data_frames={"DCF_Model": df_dcf})
    else:
        st.error("DCF Valuation could not be generated. Please check inputs.")
