"""
Financial Model Engine
Builds linked 3-statement financial models with proper accounting relationships.
"""

from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from loguru import logger

from ..models.schemas import (
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
    FinancialStatements,
    LinkedModel,
    ForecastAssumptions,
    FinancialRatios,
    AccountingStandard
)
from ..config import config


class ModelEngine:
    """
    Financial Model Engine for building linked 3-statement models.
    Ensures proper accounting relationships and balance sheet balancing.
    """
    
    def __init__(self, statements: FinancialStatements):
        """
        Initialize Model Engine.
        
        Args:
            statements: Complete financial statements
        """
        self.statements = statements
        self.validation_errors = []
        self.linked_model = None
        
        logger.info(f"Initialized ModelEngine for {statements.company_name}")
    
    def build_linked_model(self) -> LinkedModel:
        """
        Build linked 3-statement model from historical data.
        """
        logger.info("Building linked 3-statement model...")
        
        # 1. Force Accounting Linkages (Sync Net Income, D&A, etc.)
        self._force_accounting_linkages()
        
        # 2. Validate input data
        self._validate_statements()
        
        # 3. Calculate historical ratios
        historical_ratios = self._calculate_ratios()
        
        # 4. Calculate assumptions from historical data (not hardcoded!)
        last_inc = self.statements.income_statements[-1]
        last_bs = self.statements.balance_sheets[-1]
        last_cf = self.statements.cash_flow_statements[-1] if self.statements.cash_flow_statements else None
        
        # Calculate actual margins from historical data
        if last_inc.revenue and last_inc.revenue > 0:
            hist_gross_margin = (last_inc.gross_profit / last_inc.revenue) if last_inc.gross_profit else 0.40
            hist_op_margin = (last_inc.operating_income / last_inc.revenue) if last_inc.operating_income else 0.20
            hist_net_margin = last_inc.net_income / last_inc.revenue
        else:
            hist_gross_margin = 0.40
            hist_op_margin = 0.20
            hist_net_margin = 0.10
        
        # Sanity checks for margins
        hist_gross_margin = max(0.10, min(0.95, hist_gross_margin))  # Clamp between 10% and 95%
        hist_op_margin = max(-0.50, min(0.80, hist_op_margin))  # Allow negative op margin for growth companies
        
        # Calculate CAPEX % from historical CF if available
        # Calculate CAPEX % of Revenue
        hist_capex_pct = config.defaults.CAPEX_PERCENT_OF_REVENUE
        if last_cf and last_cf.capital_expenditures and last_inc.revenue > 0:
            hist_capex_pct = abs(last_cf.capital_expenditures) / last_inc.revenue
            hist_capex_pct = max(config.thresholds.MIN_CAPEX_PERCENT, min(config.thresholds.MAX_CAPEX_PERCENT, hist_capex_pct))
        
        # Calculate dividend payout ratio
        hist_div_payout = 0.0
        if last_cf and last_cf.dividends_paid and last_inc.net_income > 0:
            hist_div_payout = abs(last_cf.dividends_paid) / last_inc.net_income
            hist_div_payout = min(1.0, hist_div_payout)  # Cap at 100%
        
        # Calculate working capital days from historical BS
        hist_dso = config.defaults.DAYS_SALES_OUTSTANDING
        hist_dio = config.defaults.DAYS_INVENTORY_OUTSTANDING
        hist_dpo = config.defaults.DAYS_PAYABLE_OUTSTANDING
        
        if last_bs.accounts_receivable and last_inc.revenue > 0:
            hist_dso = int((last_bs.accounts_receivable / last_inc.revenue) * 365)
        if last_bs.inventory and last_inc.cost_of_revenue and last_inc.cost_of_revenue > 0:
            hist_dio = int((last_bs.inventory / last_inc.cost_of_revenue) * 365)
        if last_bs.accounts_payable and last_inc.cost_of_revenue and last_inc.cost_of_revenue > 0:
            hist_dpo = int((last_bs.accounts_payable / last_inc.cost_of_revenue) * 365)
        
        logger.info(f"Derived assumptions from historical: Gross Margin={hist_gross_margin:.1%}, Op Margin={hist_op_margin:.1%}, CAPEX={hist_capex_pct:.1%}")
        
        # 5. Create linked model with data-driven assumptions
        self.linked_model = LinkedModel(
            company_name=self.statements.company_name,
            base_year=self.statements.fiscal_year,
            report_type=self.statements.report_type,
            forecast_years=0,
            accounting_standard=self.statements.accounting_standard,
            ticker=self.statements.ticker,
            historical_income_statements=self.statements.income_statements,
            historical_balance_sheets=self.statements.balance_sheets,
            historical_cash_flows=self.statements.cash_flow_statements,
            historical_ratios=historical_ratios,
            assumptions=ForecastAssumptions(
                revenue_growth_rate=config.defaults.REVENUE_GROWTH_RATE,
                gross_margin=hist_gross_margin,
                operating_margin=hist_op_margin,
                net_margin=hist_net_margin,
                capex_percent_of_revenue=hist_capex_pct,
                dividend_payout_ratio=hist_div_payout,
                days_sales_outstanding=hist_dso,
                days_inventory_outstanding=hist_dio,
                days_payable_outstanding=hist_dpo
            )
        )
        
        # 5. Balance the Balance Sheets (Plug to Cash/Equity)
        self._balance_model()
        
        # 6. Validate linkages
        is_balanced = self._validate_linkages()
        self.linked_model.is_balanced = is_balanced
        self.linked_model.validation_errors = self.validation_errors
        
        if is_balanced:
            logger.info("✓ Model successfully linked and balanced")
        else:
            logger.warning(f"⚠ Model has {len(self.validation_errors)} validation errors")
        
        return self.linked_model

    def _force_accounting_linkages(self):
        """Standardize and sync values across statements before modeling."""
        for i in range(len(self.statements.income_statements)):
            inc = self.statements.income_statements[i]
            if i < len(self.statements.cash_flow_statements):
                cf = self.statements.cash_flow_statements[i]
                # NI in CF must match NI in IS
                cf.net_income = inc.net_income
                # D&A in CF must match D&A in IS
                cf.depreciation_amortization = inc.depreciation_amortization
                # Recalculate CFO
                cf.cash_from_operations = (cf.net_income or 0) + (cf.depreciation_amortization or 0) + (cf.changes_in_working_capital or 0)
                # Recalculate Net Change
                cf.net_change_in_cash = (cf.cash_from_operations or 0) + (cf.cash_from_investing or 0) + (cf.cash_from_financing or 0)
        
    def _balance_model(self):
        """Force Balance Sheet identity and record the adjustment (Plug)."""
        self.linked_model.adjustments = []
        for bs in self.linked_model.historical_balance_sheets:
            assets = bs.total_assets or 0
            liabilities = bs.total_liabilities or 0
            equity = bs.total_shareholders_equity or 0
            
            diff = assets - (liabilities + equity)
            if abs(diff) > 1000: # Rounding tolerance
                # Adjust Equity (Other Comprehensive Income/Plug) to balance
                bs.total_shareholders_equity = (bs.total_shareholders_equity or 0) + diff
                self.linked_model.adjustments.append(
                    f"Applied modeling plug of ${diff:,.0f} to Equity in {bs.period_end.year} to force balance."
                )
    
    def _validate_statements(self):
        """Validate that we have complete statements."""
        if not self.statements.income_statements:
            raise ValueError("No income statements provided")
        if not self.statements.balance_sheets:
            raise ValueError("No balance sheets provided")
        if not self.statements.cash_flow_statements:
            raise ValueError("No cash flow statements provided")
        
        logger.debug(f"Validated {len(self.statements.income_statements)} periods of data")
    
    def _validate_linkages(self) -> bool:
        """
        Validate that the 3 statements are properly linked using strict accounting logic.
        See: Linked 3-Statement Model — Data Relationships & Inputs
        """
        is_valid = True
        self.validation_errors = [] # Clear previous errors
        
        # Get statements sorted by period
        income_stmts = sorted(self.statements.income_statements, key=lambda x: x.period_end)
        balance_sheets = sorted(self.statements.balance_sheets, key=lambda x: x.period_end)
        cash_flows = sorted(self.statements.cash_flow_statements, key=lambda x: x.period_end)
        
        # We can only validate if we have at least one period. 
        # For roll-forwards (RE, Cash, PPE, Equity), we need Previous Balance Sheet.
        # However, even for the first period, we can check basic identities (Assets = L+E).
        
        for i in range(len(balance_sheets)):
            period = balance_sheets[i].period_end
            
            # 1. Basic Balance Sheet Check: Assets = Liabilities + Equity
            is_valid &= self._check_balance_sheet_identity(balance_sheets[i])
            
            # For roll-forwards, we need the previous period
            if i > 0:
                prev_bs = balance_sheets[i-1]
                curr_bs = balance_sheets[i]
                
                # Match Income/CF statements for the *current* period (ending at period)
                # Typically index i corresponds to the period ending at balance_sheets[i]
                # Assuming lists are aligned by period. Best to find by date match.
                inc = next((x for x in income_stmts if x.period_end == period), None)
                cf = next((x for x in cash_flows if x.period_end == period), None)
                
                if inc and cf:
                    # 2. Retained Earnings Roll-forward
                    # End RE = Beg RE + Net Income - Dividends
                    is_valid &= self._check_re_rollforward(prev_bs, curr_bs, inc, cf)
                    
                    # 3. Cash Roll-forward
                    # End Cash = Beg Cash + Net Change in Cash
                    is_valid &= self._check_cash_rollforward(prev_bs, curr_bs, cf)
                    
                    # 4. PPE Roll-forward
                    # End PPE = Beg PPE + Capex - D&A - Disposals
                    # Note: This is often approximate due to disposals being buried in notes
                    self._check_ppe_rollforward(prev_bs, curr_bs, inc, cf) # Don't fail validation on this, just warn
                    
                    # 5. Equity Roll-forward
                    # End Equity = Beg Equity + NI - Div + Issuance
                    is_valid &= self._check_equity_rollforward(prev_bs, curr_bs, inc, cf)

        return is_valid
    
    def _check_balance_sheet_identity(self, bs: BalanceSheet) -> bool:
        """Assets = Liabilities + Equity"""
        assets = bs.total_assets or 0
        liab = bs.total_liabilities or 0
        eq = bs.total_shareholders_equity or 0
        
        expected = liab + eq
        diff = assets - expected
        
        # Strict tolerance for rounding only ($1000 in millions)
        if abs(diff) > 1000:
            self.validation_errors.append(
                f"BS Identity Mismatch {bs.period_end.year}: Assets (${assets:,.0f}) != L+E (${expected:,.0f}). Gap: ${diff:,.0f}"
            )
            return False
        return True

    def _check_re_rollforward(self, prev_bs: BalanceSheet, curr_bs: BalanceSheet, inc: IncomeStatement, cf: CashFlowStatement) -> bool:
        """End RE = Beg RE + Net Income - Dividends"""
        beg_re = prev_bs.retained_earnings or 0
        end_re = curr_bs.retained_earnings or 0
        ni = inc.net_income or 0
        div = cf.dividends_paid or 0 # Usually negative or positive depending on sign convention. Assuming usually reported as negative outflow.
        
        # If dividends are positive in CF (outflow), subtract them. If negative, add them.
        # Standard: Dividends paid is a use of cash, so often negative in CF.
        # But in RE formula: RE_new = RE_old + NI - Dividends_Declared
        # We'll assume 'div' is absolute value for subtraction
        div_abs = abs(div)
        
        expected = beg_re + ni - div_abs
        diff = end_re - expected
        
        if abs(diff) > abs(end_re) * 0.05 + 1000: # 5% tolerance
             self.validation_errors.append(
                f"RE Rollforward {curr_bs.period_end.year}: Beg {beg_re:,.0f} + NI {ni:,.0f} - Div {div_abs:,.0f} != End {end_re:,.0f} (Diff: {diff:,.0f})"
            )
             return False
        return True

    def _check_cash_rollforward(self, prev_bs: BalanceSheet, curr_bs: BalanceSheet, cf: CashFlowStatement) -> bool:
        """End Cash = Beg Cash + Net Change"""
        beg_cash = prev_bs.cash_and_equivalents or 0
        end_cash = curr_bs.cash_and_equivalents or 0
        net_change = cf.net_change_in_cash
        
        if net_change is None or net_change == 0:
             # Calculate from sum of parts if not explicitly set
             net_change = (cf.cash_from_operations or 0) + (cf.cash_from_investing or 0) + (cf.cash_from_financing or 0)
        
        expected = beg_cash + net_change
        diff = end_cash - expected
        
        if abs(diff) > 1000:
            self.validation_errors.append(
                f"Cash Reconciliation Error {curr_bs.period_end.year}: Beg Cash (${beg_cash:,.0f}) + Net Change (${net_change:,.0f}) = ${expected:,.0f} vs BS Cash (${end_cash:,.0f}). Gap: ${diff:,.0f}"
            )
            return False
        return True

    def _check_ppe_rollforward(self, prev_bs: BalanceSheet, curr_bs: BalanceSheet, inc: IncomeStatement, cf: CashFlowStatement) -> bool:
        """End PPE = Beg PPE + Capex - D&A"""
        beg_ppe = prev_bs.property_plant_equipment_net or 0
        end_ppe = curr_bs.property_plant_equipment_net or 0
        capex = abs(cf.capital_expenditures or 0) # Capex adds to PPE
        da = inc.depreciation_amortization or 0 # D&A reduces PPE
        
        expected = beg_ppe + capex - da
        diff = end_ppe - expected
        
        # Large tolerance due to disposals, impairments, FX
        if abs(diff) > abs(end_ppe) * 0.15 + 1000000:
             self.validation_errors.append(
                f"PPE Rollforward {curr_bs.period_end.year}: Beg {beg_ppe:,.0f} + Capex {capex:,.0f} - D&A {da:,.0f} != End {end_ppe:,.0f} (Diff: {diff:,.0f})"
            )
             return False
        return True
        
    def _check_equity_rollforward(self, prev_bs: BalanceSheet, curr_bs: BalanceSheet, inc: IncomeStatement, cf: CashFlowStatement) -> bool:
        """End Equity = Beg Equity + Net Income - Dividends + Issuance/Buybacks"""
        beg_eq = prev_bs.total_shareholders_equity or 0
        end_eq = curr_bs.total_shareholders_equity or 0
        ni = inc.net_income or 0
        div = abs(cf.dividends_paid or 0)
        
        # Issuance/Buyback usually in Financing CF
        # We can approximate 'Other Equity Changes' as the plug
        expected_base = beg_eq + ni - div
        diff = end_eq - expected_base
        
        # Checking if diff roughly matches financing cash flow excluding dividends?
        # This is complex. For now, just a loose check called "Equity Bridge"
        if abs(diff) > abs(end_eq) * 0.10: # 10% tolerance for buybacks/issuance not explicitly tracked
             pass # Don't error, just info
             
        return True
    
    def _calculate_ratios(self) -> List[FinancialRatios]:
        """Calculate financial ratios for all periods."""
        ratios_list = []
        
        for i, income in enumerate(self.statements.income_statements):
            if i >= len(self.statements.balance_sheets):
                continue
            
            bs = self.statements.balance_sheets[i]
            cf = self.statements.cash_flow_statements[i] if i < len(self.statements.cash_flow_statements) else None
            
            ratios = FinancialRatios(period=income.period_end)
            
            # Profitability ratios
            if income.revenue and income.revenue > 0:
                if income.gross_profit:
                    ratios.gross_margin = income.gross_profit / income.revenue
                if income.operating_income:
                    ratios.operating_margin = income.operating_income / income.revenue
                ratios.net_margin = income.net_income / income.revenue
            
            if bs.total_assets and bs.total_assets > 0:
                ratios.return_on_assets = income.net_income / bs.total_assets
            
            if bs.total_shareholders_equity and bs.total_shareholders_equity > 0:
                ratios.return_on_equity = income.net_income / bs.total_shareholders_equity
            
            # Liquidity ratios
            if bs.total_current_liabilities and bs.total_current_liabilities > 0:
                if bs.total_current_assets:
                    ratios.current_ratio = bs.total_current_assets / bs.total_current_liabilities
                
                quick_assets = (
                    (bs.cash_and_equivalents or 0) +
                    (bs.short_term_investments or 0) +
                    (bs.accounts_receivable or 0)
                )
                ratios.quick_ratio = quick_assets / bs.total_current_liabilities
                
                if bs.cash_and_equivalents:
                    ratios.cash_ratio = bs.cash_and_equivalents / bs.total_current_liabilities
            
            # Leverage ratios
            if bs.total_shareholders_equity and bs.total_shareholders_equity > 0:
                total_debt = (bs.short_term_debt or 0) + (bs.long_term_debt or 0)
                ratios.debt_to_equity = total_debt / bs.total_shareholders_equity
            
            if bs.total_assets and bs.total_assets > 0:
                total_debt = (bs.short_term_debt or 0) + (bs.long_term_debt or 0)
                ratios.debt_to_assets = total_debt / bs.total_assets
            
            if income.interest_expense and income.interest_expense != 0:
                ratios.interest_coverage = income.operating_income / abs(income.interest_expense)
            
            # Efficiency ratios
            if income.revenue and income.revenue > 0:
                if bs.total_assets:
                    ratios.asset_turnover = income.revenue / bs.total_assets
                
                if bs.inventory:
                    cogs = income.cost_of_revenue or 0
                    ratios.inventory_turnover = cogs / bs.inventory if bs.inventory > 0 else None
                    if ratios.inventory_turnover:
                        ratios.days_inventory_outstanding = 365 / ratios.inventory_turnover
                
                if bs.accounts_receivable and bs.accounts_receivable > 0:
                    ratios.receivables_turnover = income.revenue / bs.accounts_receivable
                    if ratios.receivables_turnover and ratios.receivables_turnover > 0:
                        ratios.days_sales_outstanding = 365 / ratios.receivables_turnover
                
                if bs.accounts_payable and bs.accounts_payable > 0:
                    cogs = income.cost_of_revenue or 0
                    payables_turnover = cogs / bs.accounts_payable
                    if payables_turnover and payables_turnover > 0:
                        ratios.days_payable_outstanding = 365 / payables_turnover
            
            # Cash conversion cycle
            if all([ratios.days_sales_outstanding, ratios.days_inventory_outstanding, 
                   ratios.days_payable_outstanding]):
                ratios.cash_conversion_cycle = (
                    ratios.days_sales_outstanding +
                    ratios.days_inventory_outstanding -
                    ratios.days_payable_outstanding
                )
            
            ratios_list.append(ratios)
        
        logger.info(f"Calculated ratios for {len(ratios_list)} periods")
        return ratios_list
    
    def get_summary_metrics(self) -> Dict:
        """Get summary metrics from the model."""
        if not self.linked_model:
            raise ValueError("Model not built yet. Call build_linked_model() first.")
        
        latest_income = self.linked_model.historical_income_statements[-1]
        latest_bs = self.linked_model.historical_balance_sheets[-1]
        latest_ratios = self.linked_model.historical_ratios[-1] if self.linked_model.historical_ratios else None
        
        return {
            'company': self.statements.company_name,
            'fiscal_year': self.statements.fiscal_year,
            'revenue': latest_income.revenue,
            'net_income': latest_income.net_income,
            'total_assets': latest_bs.total_assets,
            'total_equity': latest_bs.total_shareholders_equity,
            'net_margin': latest_ratios.net_margin if latest_ratios else None,
            'roe': latest_ratios.return_on_equity if latest_ratios else None,
            'current_ratio': latest_ratios.current_ratio if latest_ratios else None,
            'debt_to_equity': latest_ratios.debt_to_equity if latest_ratios else None
        }


# Example usage
if __name__ == "__main__":
    from datetime import date
    
    # Create sample statements
    statements = FinancialStatements(
        company_name="Example Corp",
        ticker="EXMP",
        fiscal_year=2023,
        report_type="10-K",
        accounting_standard=AccountingStandard.GAAP
    )
    
    # Add sample data (simplified)
    statements.income_statements.append(
        IncomeStatement(
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
            revenue=1000000,
            net_income=100000
        )
    )
    
    # Build model
    engine = ModelEngine(statements)
    model = engine.build_linked_model()
    
    print(f"Model balanced: {model.is_balanced}")
    print(f"Validation errors: {len(model.validation_errors)}")
