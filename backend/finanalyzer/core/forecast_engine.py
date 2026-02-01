"""
Forecast Engine
Driver-based financial forecasting with scenario support.
"""

from datetime import date, timedelta
from typing import Dict, List, Optional
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np

from loguru import logger

from ..models.schemas import (
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
    LinkedModel,
    ForecastAssumptions,
    FinancialRatios,
    Currency,
    DCFYearData,
    DCFValuation
)
from ..config import config, ScenarioType, Recommendation


class ForecastEngine:
    """
    Financial forecasting engine with driver-based methodology.
    Supports multiple scenarios (base, bull, bear).
    """
    
    def __init__(self, linked_model: LinkedModel):
        """
        Initialize Forecast Engine.
        
        Args:
            linked_model: Linked historical model
        """
        self.model = linked_model
        self.forecast_years = 0
        
        logger.info(f"Initialized ForecastEngine for {linked_model.company_name}")
    
    def forecast(
        self,
        years: int = 5,
        assumptions: Optional[ForecastAssumptions] = None,
        scenario: str = "base"
    ) -> LinkedModel:
        """
        Generate financial forecast.
        
        Args:
            years: Number of years to forecast
            assumptions: Forecast assumptions (uses model defaults if None)
            scenario: Scenario type (base, bull, bear)
            
        Returns:
            Updated LinkedModel with forecasts
        """
        logger.info(f"Generating {years}-year {scenario} forecast...")
        
        self.forecast_years = years
        
        # Use provided assumptions or model defaults
        if assumptions:
            self.model.assumptions = assumptions
        
        # Adjust assumptions based on scenario
        self._adjust_for_scenario(scenario)
        
        # Validate that we have historical data to base forecast on
        if not self.model.historical_income_statements:
            raise ValueError("Cannot forecast: No historical income statements available")
        if not self.model.historical_balance_sheets:
            raise ValueError("Cannot forecast: No historical balance sheets available")
        if not self.model.historical_cash_flows:
            raise ValueError("Cannot forecast: No historical cash flow statements available")
        
        # Get base year data
        base_income = self.model.historical_income_statements[-1]
        base_bs = self.model.historical_balance_sheets[-1]
        base_cf = self.model.historical_cash_flows[-1]
        
        # Generate forecasts for each year
        for year in range(1, years + 1):
            logger.debug(f"Forecasting year {year}/{years}")
            
            # Forecast Income Statement
            forecast_income = self._forecast_income_statement(
                base_income if year == 1 else self.model.forecast_income_statements[-1],
                year
            )
            self.model.forecast_income_statements.append(forecast_income)
            
            # Forecast Balance Sheet
            forecast_bs = self._forecast_balance_sheet(
                base_bs if year == 1 else self.model.forecast_balance_sheets[-1],
                forecast_income,
                year
            )
            self.model.forecast_balance_sheets.append(forecast_bs)
            
            # Forecast Cash Flow Statement
            forecast_cf = self._forecast_cash_flow(
                forecast_income,
                base_bs if year == 1 else self.model.forecast_balance_sheets[-2],
                forecast_bs,
                year
            )
            self.model.forecast_cash_flows.append(forecast_cf)
            
            # Calculate forecast ratios
            ratios = self._calculate_forecast_ratios(
                forecast_income,
                forecast_bs,
                forecast_cf
            )
            self.model.forecast_ratios.append(ratios)
        
        self.model.forecast_years = years
        
        logger.info(f"✓ Forecast complete for {years} years")
        
        # After forecasting, generate investment advice if possible
        # We can handle this in the main app, but better to have logic here
        return self.model

    def generate_investment_advice(self, sentiment_result: Optional[dict] = None) -> LinkedModel:
        """
        Generate Stock recommendation and target price based on forecast and sentiment.
        """
        logger.info("Generating investment recommendation...")
        
        # 1. Quantitative Analysis
        last_hist = self.model.historical_income_statements[-1]
        last_fcst = self.model.forecast_income_statements[-1]
        
        if last_hist.revenue > 0 and self.model.forecast_years > 0:
            rev_growth = (last_fcst.revenue / last_hist.revenue) ** (1/self.model.forecast_years) - 1
        else:
            rev_growth = 0
            
        avg_net_margin = 0
        if self.model.forecast_income_statements:
            margins = [s.net_income / s.revenue for s in self.model.forecast_income_statements if s.revenue > 0]
            if margins:
                avg_net_margin = sum(margins) / len(margins)
        
        # 2. Valuation (DCF Model)
        mkt = self.model.market_data or {}
        dcf = self._calculate_dcf()
        self.model.dcf_valuation = dcf
        
        target_price = dcf.implied_price_per_share
        current_price = mkt.get('current_price')
        
        # 3. Sentiment Weighting
        sentiment_score = 0
        if sentiment_result:
            sentiment_score = sentiment_result.get('composite_score', 0)
            
        # 4. Recommendation Logic (Nuanced Scoring)
        score = 0
        
        # Growth points
        if rev_growth > 0.15: score += 3
        elif rev_growth > 0.08: score += 2
        elif rev_growth > 0.03: score += 1
        
        # Margin points
        if avg_net_margin > 0.20: score += 3
        elif avg_net_margin > 0.10: score += 2
        elif avg_net_margin > 0.05: score += 1
        
        # Sentiment points
        if sentiment_score > 0.2: score += 2
        elif sentiment_score > 0.05: score += 1
        elif sentiment_score < -0.2: score -= 2
        elif sentiment_score < -0.05: score -= 1

        # Valuation Adjustment (Points based on upside if current price known)
        upside = 0
        if current_price:
            upside = (target_price / current_price) - 1
            if upside > 0.4: score += 3 # Significant Undervaluation
            elif upside > 0.2: score += 2 
            elif upside > 0.05: score += 1
            elif upside < -0.3: score -= 3 # Significant Overvaluation
            elif upside < -0.15: score -= 2
            elif upside < -0.05: score -= 1
        
        # Final Decision
        if score >= 6:
            self.model.recommendation = "BUY"
            thesis = f"Strong fundamentals (Growth: {rev_growth:.1%}) combined with significant intrinsic value upside ({upside:.1%})."
        elif score >= 3:
            self.model.recommendation = "HOLD"
            thesis = f"Stable performance with fair valuation. Intrinsic value is close to current market price."
        else:
            self.model.recommendation = "SELL"
            thesis = "Valuation looks stretched relative to growth potential or intrinsic cash flow generation."
            
        self.model.target_price = target_price
        self.model.upside_potential = upside if current_price else None
        self.model.investment_thesis = thesis
        
        return self.model
    
    def _adjust_for_scenario(self, scenario: str):
        """Adjust assumptions based on scenario."""
        assumptions = self.model.assumptions
        
        if scenario == ScenarioType.BULL:
            # Optimistic scenario
            assumptions.revenue_growth_rate *= 1.5
            assumptions.gross_margin = min(assumptions.gross_margin * 1.1, config.thresholds.MAX_GROSS_MARGIN)
            assumptions.operating_margin = min(assumptions.operating_margin * 1.1, config.thresholds.MAX_OPERATING_MARGIN)
            logger.info("Applied bull scenario adjustments")
            
        elif scenario == ScenarioType.BEAR:
            # Pessimistic scenario
            assumptions.revenue_growth_rate *= 0.5
            assumptions.gross_margin *= 0.9
            assumptions.operating_margin *= 0.85
            logger.info("Applied bear scenario adjustments")
        
        else:
            logger.info("Using base scenario assumptions")
        
        # Save scenario to assumptions so it persists
        self.model.assumptions.scenario = scenario
    
    def _forecast_income_statement(
        self,
        prev_income: IncomeStatement,
        year: int
    ) -> IncomeStatement:
        """Forecast Income Statement using driver-based approach."""
        assumptions = self.model.assumptions
        
        # Calculate forecast period
        period_end = prev_income.period_end + relativedelta(years=1)
        period_start = period_end - relativedelta(years=1) + relativedelta(days=1)
        
        # Revenue forecast (key driver)
        revenue = prev_income.revenue * (1 + assumptions.revenue_growth_rate)
        
        # Cost of Revenue (based on gross margin)
        gross_profit = revenue * assumptions.gross_margin
        cost_of_revenue = revenue - gross_profit
        
        # Operating Expenses (based on operating margin)
        operating_income = revenue * assumptions.operating_margin
        operating_expenses = gross_profit - operating_income
        
        # Depreciation & Amortization (% of PPE from balance sheet)
        # Will be refined when we have PPE forecast
        depreciation_amortization = prev_income.depreciation_amortization or 0
        if depreciation_amortization > 0:
            depreciation_amortization *= (1 + assumptions.revenue_growth_rate * 0.5)
        
        # EBIT
        ebit = operating_income
        
        # Interest Expense (estimated from debt levels)
        interest_expense = prev_income.interest_expense or 0
        interest_income = prev_income.interest_income or 0
        
        # Income Before Tax
        income_before_tax = ebit + (interest_income or 0) - abs(interest_expense or 0)
        
        # Tax Expense
        income_tax_expense = income_before_tax * assumptions.tax_rate
        
        # Net Income
        net_income = income_before_tax - income_tax_expense
        
        # EPS (assuming constant shares)
        shares_outstanding = prev_income.shares_outstanding_diluted or prev_income.shares_outstanding_basic
        diluted_eps = net_income / shares_outstanding if shares_outstanding else None
        
        return IncomeStatement(
            period_start=period_start,
            period_end=period_end,
            currency=prev_income.currency,
            revenue=revenue,
            cost_of_revenue=cost_of_revenue,
            gross_profit=gross_profit,
            operating_expenses=operating_expenses,
            operating_income=operating_income,
            ebitda=operating_income + depreciation_amortization,
            depreciation_amortization=depreciation_amortization,
            ebit=ebit,
            interest_income=interest_income,
            interest_expense=interest_expense,
            income_before_tax=income_before_tax,
            income_tax_expense=income_tax_expense,
            effective_tax_rate=assumptions.tax_rate,
            net_income=net_income,
            diluted_eps=diluted_eps,
            shares_outstanding_diluted=shares_outstanding
        )
    
    def _forecast_balance_sheet(
        self,
        prev_bs: BalanceSheet,
        forecast_income: IncomeStatement,
        year: int
    ) -> BalanceSheet:
        """Forecast Balance Sheet with proper linking."""
        assumptions = self.model.assumptions
        period_end = forecast_income.period_end
        
        # === ASSETS ===
        
        # Working Capital Items (driver-based)
        revenue = forecast_income.revenue
        cogs = forecast_income.cost_of_revenue or 0
        
        # Accounts Receivable (DSO)
        accounts_receivable = (revenue / 365) * assumptions.days_sales_outstanding
        
        # Inventory (DIO)
        inventory = (cogs / 365) * assumptions.days_inventory_outstanding
        
        # Accounts Payable (DPO)
        accounts_payable = (cogs / 365) * assumptions.days_payable_outstanding
        
        # Cash (plug for now, will be refined with cash flow)
        cash_and_equivalents = prev_bs.cash_and_equivalents or 0
        
        # Other current assets (grow with revenue)
        growth_rate = assumptions.revenue_growth_rate
        other_current_assets = (prev_bs.other_current_assets or 0) * (1 + growth_rate)
        prepaid_expenses = (prev_bs.prepaid_expenses or 0) * (1 + growth_rate)
        
        # Total Current Assets
        total_current_assets = (
            cash_and_equivalents +
            (prev_bs.short_term_investments or 0) +
            accounts_receivable +
            inventory +
            prepaid_expenses +
            other_current_assets
        )
        
        # PPE (Beginning PPE + CAPEX - D&A)
        capex = revenue * assumptions.capex_percent_of_revenue
        da = forecast_income.depreciation_amortization or 0
        ppe_net = (prev_bs.property_plant_equipment_net or 0) + capex - da
        
        # Other non-current assets (grow with revenue)
        intangible_assets = (prev_bs.intangible_assets or 0) * (1 + growth_rate * 0.5)
        goodwill = prev_bs.goodwill or 0  # Constant unless acquisition
        other_non_current = (prev_bs.other_non_current_assets or 0) * (1 + growth_rate * 0.3)
        
        total_non_current_assets = (
            ppe_net +
            intangible_assets +
            goodwill +
            (prev_bs.long_term_investments or 0) +
            other_non_current
        )
        
        # === LIABILITIES ===
        
        # Current Liabilities
        short_term_debt = prev_bs.short_term_debt or 0
        accrued_expenses = (prev_bs.accrued_expenses or 0) * (1 + growth_rate)
        deferred_revenue = (prev_bs.deferred_revenue or 0) * (1 + growth_rate)
        other_current_liabilities = (prev_bs.other_current_liabilities or 0) * (1 + growth_rate)
        
        total_current_liabilities = (
            accounts_payable +
            short_term_debt +
            accrued_expenses +
            deferred_revenue +
            other_current_liabilities
        )
        
        # Non-Current Liabilities
        long_term_debt = prev_bs.long_term_debt or 0
        deferred_tax_liabilities = (prev_bs.deferred_tax_liabilities or 0) * (1 + growth_rate * 0.2)
        other_non_current_liabilities = (prev_bs.other_non_current_liabilities or 0) * (1 + growth_rate * 0.2)
        
        total_non_current_liabilities = (
            long_term_debt +
            deferred_tax_liabilities +
            other_non_current_liabilities
        )
        
        total_liabilities = total_current_liabilities + total_non_current_liabilities
        
        # === EQUITY ===
        
        # Retained Earnings (Beginning RE + Net Income - Dividends)
        beginning_re = prev_bs.retained_earnings or 0
        net_income = forecast_income.net_income
        dividends = 0  # Can be added based on payout ratio
        if assumptions.dividend_payout_ratio:
            dividends = net_income * assumptions.dividend_payout_ratio
        
        retained_earnings = beginning_re + net_income - dividends
        
        # Other equity items (mostly constant)
        common_stock = prev_bs.common_stock or 0
        additional_paid_in_capital = prev_bs.additional_paid_in_capital or 0
        treasury_stock = prev_bs.treasury_stock or 0
        aoci = prev_bs.accumulated_other_comprehensive_income or 0
        
        total_shareholders_equity = (
            common_stock +
            additional_paid_in_capital +
            retained_earnings +
            (treasury_stock or 0) +
            aoci
        )
        
        # Total Assets (must equal L + E)
        total_assets = total_current_assets + total_non_current_assets
        
        # Balance check and plug to cash if needed
        balance_diff = total_assets - (total_liabilities + total_shareholders_equity)
        if abs(balance_diff) > 1:
            cash_and_equivalents += balance_diff
            total_current_assets += balance_diff
            total_assets += balance_diff
        
        return BalanceSheet(
            period_end=period_end,
            currency=prev_bs.currency,
            cash_and_equivalents=cash_and_equivalents,
            short_term_investments=prev_bs.short_term_investments,
            accounts_receivable=accounts_receivable,
            inventory=inventory,
            prepaid_expenses=prepaid_expenses,
            other_current_assets=other_current_assets,
            total_current_assets=total_current_assets,
            property_plant_equipment_net=ppe_net,
            intangible_assets=intangible_assets,
            goodwill=goodwill,
            long_term_investments=prev_bs.long_term_investments,
            other_non_current_assets=other_non_current,
            total_non_current_assets=total_non_current_assets,
            total_assets=total_assets,
            accounts_payable=accounts_payable,
            short_term_debt=short_term_debt,
            accrued_expenses=accrued_expenses,
            deferred_revenue=deferred_revenue,
            other_current_liabilities=other_current_liabilities,
            total_current_liabilities=total_current_liabilities,
            long_term_debt=long_term_debt,
            deferred_tax_liabilities=deferred_tax_liabilities,
            other_non_current_liabilities=other_non_current_liabilities,
            total_non_current_liabilities=total_non_current_liabilities,
            total_liabilities=total_liabilities,
            common_stock=common_stock,
            additional_paid_in_capital=additional_paid_in_capital,
            retained_earnings=retained_earnings,
            treasury_stock=treasury_stock,
            accumulated_other_comprehensive_income=aoci,
            total_shareholders_equity=total_shareholders_equity
        )
    
    def _forecast_cash_flow(
        self,
        forecast_income: IncomeStatement,
        prev_bs: BalanceSheet,
        forecast_bs: BalanceSheet,
        year: int
    ) -> CashFlowStatement:
        """Forecast Cash Flow Statement."""
        period_end = forecast_income.period_end
        period_start = period_end - relativedelta(years=1) + relativedelta(days=1)
        
        # Operating Activities
        net_income = forecast_income.net_income
        da = forecast_income.depreciation_amortization or 0
        
        # Changes in Working Capital
        change_receivables = (forecast_bs.accounts_receivable or 0) - (prev_bs.accounts_receivable or 0)
        change_inventory = (forecast_bs.inventory or 0) - (prev_bs.inventory or 0)
        change_payables = (forecast_bs.accounts_payable or 0) - (prev_bs.accounts_payable or 0)
        
        changes_in_wc = -change_receivables - change_inventory + change_payables
        
        cash_from_operations = net_income + da + changes_in_wc
        
        # Investing Activities
        capex = -self.model.assumptions.capex_percent_of_revenue * forecast_income.revenue
        cash_from_investing = capex
        
        # Financing Activities
        dividends = 0
        if self.model.assumptions.dividend_payout_ratio:
            dividends = -net_income * self.model.assumptions.dividend_payout_ratio
        
        cash_from_financing = dividends
        
        # Net Change in Cash
        net_change = cash_from_operations + cash_from_investing + cash_from_financing
        
        cash_beginning = prev_bs.cash_and_equivalents or 0
        cash_ending = forecast_bs.cash_and_equivalents or 0
        
        return CashFlowStatement(
            period_start=period_start,
            period_end=period_end,
            currency=forecast_income.currency,
            net_income=net_income,
            depreciation_amortization=da,
            changes_in_working_capital=changes_in_wc,
            change_in_receivables=change_receivables,
            change_in_inventory=change_inventory,
            change_in_payables=change_payables,
            cash_from_operations=cash_from_operations,
            capital_expenditures=capex,
            cash_from_investing=cash_from_investing,
            dividends_paid=dividends,
            cash_from_financing=cash_from_financing,
            net_change_in_cash=net_change,
            cash_beginning_of_period=cash_beginning,
            cash_end_of_period=cash_ending
        )
    
    def _calculate_forecast_ratios(
        self,
        income: IncomeStatement,
        bs: BalanceSheet,
        cf: CashFlowStatement
    ) -> FinancialRatios:
        """Calculate ratios for forecast period."""
        ratios = FinancialRatios(period=income.period_end)
        
        # Profitability
        if income.revenue and income.revenue > 0:
            ratios.gross_margin = income.gross_profit / income.revenue if income.gross_profit is not None else None
            ratios.operating_margin = income.operating_income / income.revenue if income.operating_income is not None else None
            ratios.net_margin = income.net_income / income.revenue
        
        if bs.total_assets > 0:
            ratios.return_on_assets = income.net_income / bs.total_assets
        
        if bs.total_shareholders_equity and bs.total_shareholders_equity > 0:
            ratios.return_on_equity = income.net_income / bs.total_shareholders_equity
        
        # Liquidity
        if bs.total_current_liabilities and bs.total_current_liabilities > 0:
            ratios.current_ratio = bs.total_current_assets / bs.total_current_liabilities
        
        # Leverage
        if bs.total_shareholders_equity and bs.total_shareholders_equity > 0:
            total_debt = (bs.short_term_debt or 0) + (bs.long_term_debt or 0)
            ratios.debt_to_equity = total_debt / bs.total_shareholders_equity
        
        return ratios

    def _calculate_dcf(self) -> DCFValuation:
        """
        Calculate full DCF Valuation based on forecasted cash flows.
        """
        logger.info("Calculating DCF valuation...")
        
        assumptions = self.model.assumptions
        wacc = self._estimate_wacc()
        g = assumptions.terminal_growth_rate or 0.02
        tax_rate = assumptions.tax_rate or 0.21
        
        # Calculate FCF for forecast period
        forecast_period_data = []
        sum_pv_fcf = 0
        
        # We need historical balance sheet for NWC changes (year 1)
        prev_bs = self.model.historical_balance_sheets[-1]
        
        for i, (inc, bs, cf) in enumerate(zip(
            self.model.forecast_income_statements,
            self.model.forecast_balance_sheets,
            self.model.forecast_cash_flows
        )):
            year_num = i + 1
            
            # 1. EBIT * (1 - T)
            ebit = inc.operating_income or 0
            tax_exp = ebit * tax_rate
            nopat = ebit - tax_exp
            
            # 2. Free Cash Flow to Firm (FCFF)
            da = inc.depreciation_amortization or 0
            capex = abs(cf.capital_expenditures or 0)
            
            # Delta NWC
            curr_nwc = (bs.total_current_assets or 0) - (bs.total_current_liabilities or 0)
            prev_nwc = (prev_bs.total_current_assets or 0) - (prev_bs.total_current_liabilities or 0)
            delta_nwc = curr_nwc - prev_nwc
            
            fcf = nopat + da - capex - delta_nwc
            
            # 3. Discounting
            discount_factor = 1 / ((1 + wacc) ** year_num)
            pv_fcf = fcf * discount_factor
            
            sum_pv_fcf += pv_fcf
            
            forecast_period_data.append(DCFYearData(
                year=inc.period_end.year,
                ebit=ebit,
                tax_expense=tax_exp,
                nopat=nopat,
                depreciation_amortization=da,
                capex=capex,
                change_in_nwc=delta_nwc,
                free_cash_flow=fcf,
                discount_factor=discount_factor,
                pv_of_fcf=pv_fcf
            ))
            
            prev_bs = bs # Update for next year
            
        # 4. Terminal Value (Perpetuity Growth)
        last_fcf = forecast_period_data[-1].free_cash_flow
        
        # CRITICAL: WACC must be significantly higher than terminal growth
        if wacc <= g + 0.005:
            wacc = g + 0.02
            logger.warning(f"Adjusted WACC to {wacc:.1%} to prevent DCF explosion.")
            
        terminal_value = (last_fcf * (1 + g)) / (wacc - g)
        pv_terminal_value = terminal_value / ((1 + wacc) ** len(forecast_period_data))
        
        # 5. Enterprise Value to Equity Value
        enterprise_value = sum_pv_fcf + pv_terminal_value
        
        # Bridges
        latest_bs = self.model.historical_balance_sheets[-1]
        cash = latest_bs.cash_and_equivalents or 0
        debt = (latest_bs.short_term_debt or 0) + (latest_bs.long_term_debt or 0)
        net_debt = debt - cash
        
        equity_value = enterprise_value - net_debt
        
        # Sanity Check for negative valuation
        # Sanity Check for negative valuation
        if equity_value < 0:
            logger.warning(f"Calculated negative equity value: {equity_value}. Clamping to 0 for valuation.")
            # We could raise NegativeValuationError here if we wanted strict mode
            equity_value = 0
            
        mkt = self.model.market_data or {}
        
        # Get shares from multiple sources with proper fallback chain
        shares = mkt.get('shares_outstanding')
        
        if not shares or shares <= 0:
            latest_inc = self.model.historical_income_statements[-1]
            shares = latest_inc.shares_outstanding_diluted or latest_inc.shares_outstanding_basic or 0
        
        if not shares or shares <= 0:
            if self.model.forecast_income_statements:
                fc_inc = self.model.forecast_income_statements[-1]
                shares = fc_inc.shares_outstanding_diluted or fc_inc.shares_outstanding_basic or 0
        
        # Handle unit conversion for shares if they seem to be in millions/thousands
        # (This is a safety check if they weren't scaled during extraction)
        if shares > 0 and shares < 20000: # 20k shares is tiny for a public company
             # Likely reported in millions
             original_shares = shares
             shares *= 1e6
             logger.info(f"DCF Safety Scaling: Converted shares from millions: {original_shares:,.2f}M -> {shares:,.0f}")
        
        implied_price = equity_value / shares if shares > 0 else 0
        
        logger.info(f"DCF: Equity Value=${equity_value/1e6:,.0f}M, Shares={shares/1e6:,.1f}M, Implied Price=${implied_price:,.2f}")
        
        # Final Sanity Check for Target Price
        if implied_price > config.thresholds.MAX_REASONABLE_STOCK_PRICE:
            if mkt.get('current_price') and implied_price > mkt['current_price'] * 10:
                logger.warning(f"Target price {implied_price} seems unrealistic. Capping.")
                implied_price = mkt['current_price'] * 2.0
        
        return DCFValuation(
            forecast_period_fcf=forecast_period_data,
            sum_pv_fcf=sum_pv_fcf,
            terminal_value=terminal_value,
            pv_terminal_value=pv_terminal_value,
            enterprise_value=enterprise_value,
            net_debt=net_debt,
            equity_value=equity_value,
            shares_outstanding=shares,
            implied_price_per_share=implied_price,
            wacc_used=wacc,
            terminal_growth_used=g
        )

    def _estimate_wacc(self) -> float:
        """Estimate WACC based on market data or conservative defaults."""
        mkt = self.model.market_data or {}
        assumptions = self.model.assumptions
    
        # Check for direct WACC override from sensitivity analysis or manual setting
        if hasattr(assumptions, 'wacc') and assumptions.wacc is not None and assumptions.wacc > 0:
            return assumptions.wacc

        # Cost of Equity (CAPM)
        rf = assumptions.risk_free_rate or 0.04
        erp = assumptions.equity_risk_premium or 0.05
        beta = mkt.get('beta') or assumptions.beta or 1.0
        
        cost_of_equity = rf + (beta * erp)
        
        # Cost of Debt
        cost_of_debt = assumptions.cost_of_debt or 0.05
        tax_rate = assumptions.tax_rate or 0.21
        after_tax_cost_of_debt = cost_of_debt * (1 - tax_rate)
        
        # Capital Structure
        latest_bs = self.model.historical_balance_sheets[-1]
        debt = (latest_bs.short_term_debt or 0) + (latest_bs.long_term_debt or 0)
        equity = latest_bs.total_shareholders_equity or 1e9
        
        # Use market cap for equity if available
        market_cap = mkt.get('market_cap')
        if market_cap:
            equity = market_cap
            
        total_cap = debt + equity
        w_equity = equity / total_cap if total_cap > 0 else 1.0
        w_debt = 1.0 - w_equity
        
        wacc = (w_equity * cost_of_equity) + (w_debt * after_tax_cost_of_debt)
        
        # Safe default if estimation yields 0 or suspiciously low (prevents $0 DCF)
        if wacc < 0.05:
            wacc = 0.085 # 8.5% is a standard safe default
            
        return wacc

    def calculate_reverse_dcf(self, target_valuation: float, target_irr: float = 0.25) -> 'ReverseDCFAnalysis':
        """
        Perform Reverse DCF to find required growth rate for a target valuation.
        Iteratively adjusts revenue growth until EV matches target.
        """
        logger.info(f"Calculating Reverse DCF for target valuation: ${target_valuation:,.0f}")
        
        from ..models.schemas import ReverseDCFAnalysis
        
        # Save original assumptions
        original_growth = self.model.assumptions.revenue_growth_rate
        
        # Binary search for growth rate
        low = -0.5
        high = 5.0 # Max 500% growth
        periods = 20
        required_growth = 0
        
        for _ in range(periods):
            mid = (low + high) / 2
            self.model.assumptions.revenue_growth_rate = mid
            
            # Re-run forecast (simplified, just income needs update mainly)
            # Full forecast is expensive, maybe just approximation?
            # For now, let's just trigger a forecast (it's fast enough 5 years)
            self.forecast(years=self.forecast_years, assumptions=self.model.assumptions)
            dcf = self._calculate_dcf()
            
            if dcf.enterprise_value < target_valuation:
                low = mid
            else:
                high = mid
            
            required_growth = mid
            
        # Restore original
        self.model.assumptions.revenue_growth_rate = original_growth
        # Re-run base case
        self.forecast(years=self.forecast_years, assumptions=self.model.assumptions)
        
        # Calculate implied multiple
        current_rev = self.model.historical_income_statements[-1].revenue
        multiple = target_valuation / current_rev if current_rev else 0
        
        # Breakeven (when FCF turns positive)
        # Note: CashFlowStatement object does not have free_cash_flow field directly.
        # We can approximate by checking if net change in cash is positive or simple OpCF.
        # For true FCF, we need to inspect the DCFValuation object, but let's check OpCF here.
        breakeven_year = None
        for i, cf in enumerate(self.model.forecast_cash_flows):
            if cf.cash_from_operations > 0: # Simple check for positive cash generation
                breakeven_year = i + 1
                break
                
        return ReverseDCFAnalysis(
            target_price=target_valuation,
            required_growth_rate=required_growth,
            required_margin=self.model.assumptions.net_margin or 0.1, # Approx
            years_to_breakeven=breakeven_year,
            implied_arr_multiple=multiple
        )

# Example usage
if __name__ == "__main__":
    pass
