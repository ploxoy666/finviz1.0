"""
Quick Market Pulse UI Module.
Handles the fast analysis mode using only market data.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from ..config import config, AnalysisMode
from ..core.market_data import MarketDataProvider
from .components import apply_custom_css

def render_market_pulse():
    """Render the Quick Market Pulse dashboard."""
    st.markdown("## 🔎 Market Pulse & Technicals")
    st.info("Get immediate technical signals, peer comparisons, and price predictions just by entering a ticker.")
    
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        quick_ticker = st.text_input("Enter Stock Ticker (e.g., TSLA, NVDA)", value="", placeholder="AAPL").upper()
    
    with col_btn:
        st.write("") # Spacer
        st.write("") 
        analyze_btn = st.button("🚀 Analyze Market Pulse")
    
    # Check if analysis was triggered or results exist
    if analyze_btn and quick_ticker:
        with st.spinner(f"Fetching market data for {quick_ticker}..."):
            m_data = MarketDataProvider.fetch_data(quick_ticker)
            
            if m_data and m_data.get('current_price'):
                st.session_state.market_data = m_data
                st.session_state.pulse_ticker = quick_ticker
                
                # Fetch history for charts
                hist_df = MarketDataProvider.fetch_historical_with_indicators(quick_ticker)
                st.session_state.pulse_history = hist_df
                
                st.success(f"Analysis ready for {quick_ticker}")
            else:
                st.error("Could not fetch data for this ticker. Please check the symbol.")
    
    # Display Results if available
    if "pulse_ticker" in st.session_state and st.session_state.get("market_data"):
        data = st.session_state.market_data
        df = st.session_state.get("pulse_history")
        
        # 1. Top Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current Price", f"${data.get('current_price', 0):.2f}")
        m2.metric("Market Cap", f"${(data.get('market_cap') or 0)/1e9:.1f}B")
        m3.metric("P/E Ratio", f"{data.get('forward_pe', 0):.1f}x")
        m4.metric("Div Yield", f"{(data.get('dividend_yield', 0) or 0)*100:.2f}%")
        
        st.markdown("---")
        
        # 2. Charts & Technicals
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.subheader("Price Action & Indicators")
            if df is not None and not df.empty:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df.index,
                                open=df['Open'], high=df['High'],
                                low=df['Low'], close=df['Close'], name='Price'))
                
                # Add SMAs
                if 'SMA_50' in df.columns:
                    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name='SMA 50', line=dict(color='orange', width=1)))
                if 'SMA_200' in df.columns:
                    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], name='SMA 200', line=dict(color='blue', width=1)))
                    
                fig.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0), template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No historical data available for chart.")
                
        with c2:
            st.subheader("Technical Signal")
            
            # Simple technical logic
            rsi = df['RSI'].iloc[-1] if df is not None and 'RSI' in df.columns else 50
            price = data.get('current_price', 0)
            sma200 = df['SMA_200'].iloc[-1] if df is not None and 'SMA_200' in df.columns else price
            
            signal = "NEUTRAL"
            color = "gray"
            
            if rsi < 30:
                signal = "OVERSOLD (BUY WATCH)"
                color = "#4ade80" # Green
            elif rsi > 70:
                signal = "OVERBOUGHT (CAUTION)"
                color = "#f87171" # Red
            elif price > sma200:
                signal = "BULLISH TREND"
                color = "#4ade80" # Green
            else:
                signal = "BEARISH TREND"
                color = "#fb923c" # Orange
                
            # Styling: Dark Card to fix visibility issues
            st.markdown(f"""
            <div style="
                text-align: center; 
                padding: 25px; 
                background: rgba(30, 41, 59, 0.8); 
                border: 1px solid rgba(255, 255, 255, 0.1); 
                border-radius: 12px; 
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                color: white;
                margin-top: 20px;
                backdrop-filter: blur(10px);
            ">
                <h3 style="color: {color}; margin-bottom: 10px; font-weight: 800; font-size: 1.5rem;">{signal}</h3>
                <div style="font-size: 1.1rem; margin-bottom: 5px;">RSI (14): <b>{rsi:.1f}</b></div>
                <div style="font-size: 1.1rem;">vs SMA 200: <b>{((price/sma200)-1)*100:+.1f}%</b></div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        
        # 3. Peer Comparison
        st.subheader("🧬 Sector Peer Comparison")
        peers = MarketDataProvider.fetch_peers(st.session_state.pulse_ticker)
        if peers:
            peer_data_list = []
            # Add target company first
            peers_to_show = [st.session_state.pulse_ticker] + peers[:4]
            
            # Fetch data for all (could be slow, limit to 4-5)
            # Use progress 
            
            for p_ticker in peers_to_show:
                if p_ticker == st.session_state.pulse_ticker:
                    p_data = data
                else:
                    p_data = MarketDataProvider.fetch_data(p_ticker)
                
                if p_data:
                     pe = p_data.get('forward_pe', 0) or 0
                     mc = (p_data.get('market_cap') or 0) / 1e9
                     dy = (p_data.get('dividend_yield') or 0) * 100
                     price = p_data.get('current_price', 0)
                     
                     peer_data_list.append({
                         "Ticker": p_ticker,
                         "P/E Ratio": pe, 
                         "Market Cap ($B)": mc,
                         "Dividend Yield (%)": dy, 
                         "Price ($)": price
                     })
            
            if peer_data_list:
                df_peers = pd.DataFrame(peer_data_list)
                
                # Visualizations (Chart Mode)
                pc1, pc2 = st.columns(2)
                
                with pc1:
                    # Bar Chart of P/E
                    fig_pe = px.bar(
                        df_peers, 
                        x="Ticker", 
                        y="P/E Ratio", 
                        title="P/E Valuation Comparison",
                        color="Ticker",
                        text_auto='.1f',
                        template="plotly_dark"
                    )
                    fig_pe.update_layout(showlegend=False, height=300)
                    st.plotly_chart(fig_pe, use_container_width=True)
                    
                with pc2:
                    # Pie Chart of Market Cap
                    fig_mc = px.pie(
                        df_peers, 
                        values="Market Cap ($B)", 
                        names="Ticker", 
                        title="Market Cap Size Distribution",
                        hole=0.4,
                        template="plotly_dark"
                    )
                    fig_mc.update_layout(height=300)
                    st.plotly_chart(fig_mc, use_container_width=True)
                
                # Detailed Table below
                with st.expander("View Detailed Comparison Table"):
                    st.dataframe(df_peers.set_index("Ticker").style.highlight_max(axis=0), use_container_width=True)
        else:
            st.info("No peer data available for this ticker.")
            
        st.markdown("---")

        # 4. Markov Chain Analysis
        st.subheader("🎲 Markov Chain Probability Model")
        
        # UI Controls for Markov
        m_col1, m_col2 = st.columns([1, 3])
        with m_col1:
            st.markdown("##### ⚙️ Settings")
            m_days = st.slider("Forecast Days", 1, 30, 5)
            
            with st.expander("Advanced Config", expanded=False):
                m_period = st.selectbox("Data Period", ["1y", "2y", "5y", "max"], index=1)
                m_states = st.slider("Number of States", 3, 10, 5, help="Granularity of price movements")
                m_method = st.selectbox("Discretization", ["returns", "price", "quantile"], index=0, help="Method to define states")
            
            if st.button("Run Markov Analysis", type="primary"):
                try:
                    from ..core.markov_integration import run_markov_chain_analysis
                    with st.spinner("Calculating transition matrices..."):
                        logs, preds, m_data, viz, disc, mc = run_markov_chain_analysis(
                            st.session_state.pulse_ticker, 
                            n_days=m_days,
                            period=m_period,
                            n_states=m_states,
                            method=m_method
                        )
                        st.session_state.markov_results = {
                            "logs": logs, "preds": preds, "viz": viz, 
                            "config": {"days": m_days, "period": m_period}
                        }
                except ImportError:
                    st.error("Markov Integration module not found.")
                except Exception as e:
                    st.error(f"Markov Error: {e}")

        with m_col2:
            if st.session_state.get("markov_results"):
                res = st.session_state.markov_results
                
                # Show key prediction
                if res['preds']:
                    # Use actual forecast days from result/config if available, else slider
                    res_days = res.get('config', {}).get('days', m_days)
                    
                    if res_days == 1:
                        exp_price = res['preds']['expected_price']
                        move = res['preds']['expected_move_pct']
                        st.metric(f"Next Day Expectation", f"${exp_price:.2f}", f"{move:+.2f}%")
                        
                        # Probabilities chart
                        if 'probabilities' in res['preds']:
                            probs = res['preds']['probabilities']
                            fig_p = go.Figure(go.Bar(
                                x=['Bear', 'Flat', 'Bull'], 
                                y=[probs.get('down', 0), probs.get('flat', 0), probs.get('up', 0)],
                                marker_color=['#ef4444', '#94a3b8', '#22c55e']
                            ))
                            fig_p.update_layout(title="Movement Probability", height=200, template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
                            st.plotly_chart(fig_p, use_container_width=True)
                            
                    else: # Multi-day
                        final = res['preds']['daily_predictions'][-1]
                        st.metric(f"{res_days}-Day Forecast Target", f"${final['expected_price']:.2f}")
                        
                        # Plot trajectory
                        daily_df = pd.DataFrame(res['preds']['daily_predictions'])
                        fig_m = go.Figure()
                        fig_m.add_trace(go.Scatter(
                            x=daily_df['day'], 
                            y=daily_df['expected_price'], 
                            name="Expected Path",
                            line=dict(color='#3b82f6', width=3)
                        ))
                        # Add current price as start point
                        current_p = st.session_state.market_data.get('current_price')
                        if current_p:
                             fig_m.add_trace(go.Scatter(x=[0], y=[current_p], mode='markers', name='Start', marker=dict(color='white', size=8)))

                        fig_m.update_layout(template="plotly_dark", height=300, title="Expected Price Trajectory", margin=dict(l=20, r=20, t=40, b=20))
                        st.plotly_chart(fig_m, use_container_width=True)
                
                # Run Configuration Summary (Cleaner UI)
                st.caption("Analysis Configuration")
                conf = res.get('config', {})
                cfg_col1, cfg_col2, cfg_col3 = st.columns(3)
                cfg_col1.markdown(f"**Period:** {conf.get('period', 'N/A')}")
                cfg_col2.markdown(f"**States:** {m_states}") # Current slider value
                cfg_col3.markdown(f"**Method:** {m_method}") # Current select value
                
                with st.expander("🛠️ View Debug Logs", expanded=False):
                    st.code(res['logs'], language="text")
