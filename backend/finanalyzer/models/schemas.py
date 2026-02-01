"""
Data models and schemas for financial statements.
"""

from datetime import date
from enum import Enum
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator

from ..config import config


class AccountingStandard(str, Enum):
    """Accounting standards enumeration."""
    GAAP = "GAAP"
    IFRS = "IFRS"
    UNKNOWN = "UNKNOWN"


class ReportType(str, Enum):
    """Financial report type enumeration."""
    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    ANNUAL_REPORT = "Annual Report"
    QUARTERLY_REPORT = "Quarterly Report"
    IFRS_ANNUAL = "IFRS Annual"
    IFRS_INTERIM = "IFRS Interim"


class Currency(str, Enum):
    """Currency enumeration."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CNY = "CNY"
    OTHER = "OTHER"


class LineItem(BaseModel):
    """Individual line item in financial statement."""
    name: str
    value: float
    period: date
    currency: Currency = Currency.USD
    notes: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Revenue",
                "value": 1000000.0,
                "period": "2023-12-31",
                "currency": "USD"
            }
        }


class IncomeStatement(BaseModel):
    """Income Statement (P&L) data model."""
    period_start: date
    period_end: date
    currency: Currency = Currency.USD
    
    # Revenue
    revenue: float = Field(..., description="Total revenue/sales")
    cost_of_revenue: Optional[float] = Field(None, description="Cost of goods sold (COGS)")
    gross_profit: Optional[float] = None
    
    # Operating Expenses
    research_development: Optional[float] = None
    selling_general_admin: Optional[float] = None
    operating_expenses: Optional[float] = None
    
    # Operating Income
    operating_income: Optional[float] = None
    ebitda: Optional[float] = None
    depreciation_amortization: Optional[float] = None
    ebit: Optional[float] = None
    
    # Non-Operating Items
    interest_income: Optional[float] = None
    interest_expense: Optional[float] = None
    other_income_expense: Optional[float] = None
    
    # Pre-Tax & Tax
    income_before_tax: Optional[float] = None
    income_tax_expense: Optional[float] = None
    effective_tax_rate: Optional[float] = None
    
    # Net Income
    net_income: float = Field(..., description="Net income/profit")
    
    # Per Share Data
    basic_eps: Optional[float] = None
    diluted_eps: Optional[float] = None
    shares_outstanding_basic: Optional[float] = None
    shares_outstanding_diluted: Optional[float] = None
    
    # Additional Items
    line_items: List[LineItem] = Field(default_factory=list)
    
    @validator('gross_profit', always=True)
    def calculate_gross_profit(cls, v, values):
        if v is None and 'revenue' in values and 'cost_of_revenue' in values:
            if values['cost_of_revenue'] is not None:
                return values['revenue'] - values['cost_of_revenue']
        return v


class BalanceSheet(BaseModel):
    """Balance Sheet data model."""
    period_end: date
    currency: Currency = Currency.USD
    
    # Current Assets
    cash_and_equivalents: Optional[float] = None
    short_term_investments: Optional[float] = None
    accounts_receivable: Optional[float] = None
    inventory: Optional[float] = None
    prepaid_expenses: Optional[float] = None
    other_current_assets: Optional[float] = None
    total_current_assets: Optional[float] = None
    
    # Non-Current Assets
    property_plant_equipment_gross: Optional[float] = None
    accumulated_depreciation: Optional[float] = None
    property_plant_equipment_net: Optional[float] = None
    intangible_assets: Optional[float] = None
    goodwill: Optional[float] = None
    long_term_investments: Optional[float] = None
    other_non_current_assets: Optional[float] = None
    total_non_current_assets: Optional[float] = None
    
    # Total Assets
    total_assets: float = Field(..., description="Total assets")
    
    # Current Liabilities
    accounts_payable: Optional[float] = None
    short_term_debt: Optional[float] = None
    current_portion_long_term_debt: Optional[float] = None
    accrued_expenses: Optional[float] = None
    deferred_revenue: Optional[float] = None
    other_current_liabilities: Optional[float] = None
    total_current_liabilities: Optional[float] = None
    
    # Non-Current Liabilities
    long_term_debt: Optional[float] = None
    deferred_tax_liabilities: Optional[float] = None
    pension_obligations: Optional[float] = None
    other_non_current_liabilities: Optional[float] = None
    total_non_current_liabilities: Optional[float] = None
    
    # Total Liabilities
    total_liabilities: Optional[float] = None
    
    # Shareholders' Equity
    common_stock: Optional[float] = None
    additional_paid_in_capital: Optional[float] = None
    retained_earnings: Optional[float] = None
    treasury_stock: Optional[float] = None
    accumulated_other_comprehensive_income: Optional[float] = None
    total_shareholders_equity: Optional[float] = None
    
    # Additional Items
    line_items: List[LineItem] = Field(default_factory=list)
    
    @validator('total_shareholders_equity', always=True)
    def calculate_equity(cls, v, values):
        if v is None and 'total_assets' in values and 'total_liabilities' in values:
            if values['total_liabilities'] is not None:
                return values['total_assets'] - values['total_liabilities']
        return v


class CashFlowStatement(BaseModel):
    """Cash Flow Statement data model."""
    period_start: date
    period_end: date
    currency: Currency = Currency.USD
    
    # Operating Activities
    net_income: Optional[float] = None
    depreciation_amortization: Optional[float] = None
    stock_based_compensation: Optional[float] = None
    deferred_taxes: Optional[float] = None
    changes_in_working_capital: Optional[float] = None
    change_in_receivables: Optional[float] = None
    change_in_inventory: Optional[float] = None
    change_in_payables: Optional[float] = None
    other_operating_activities: Optional[float] = None
    cash_from_operations: float = Field(..., description="Net cash from operating activities")
    
    # Investing Activities
    capital_expenditures: Optional[float] = None
    acquisitions: Optional[float] = None
    purchases_of_investments: Optional[float] = None
    sales_of_investments: Optional[float] = None
    other_investing_activities: Optional[float] = None
    cash_from_investing: Optional[float] = None
    
    # Financing Activities
    debt_issuance: Optional[float] = None
    debt_repayment: Optional[float] = None
    common_stock_issued: Optional[float] = None
    common_stock_repurchased: Optional[float] = None
    dividends_paid: Optional[float] = None
    other_financing_activities: Optional[float] = None
    cash_from_financing: Optional[float] = None
    
    # Net Change
    net_change_in_cash: Optional[float] = None
    cash_beginning_of_period: Optional[float] = None
    cash_end_of_period: Optional[float] = None
    
    # Supplemental
    interest_paid: Optional[float] = None
    taxes_paid: Optional[float] = None
    
    # Additional Items
    line_items: List[LineItem] = Field(default_factory=list)


class FinancialStatements(BaseModel):
    """Complete set of financial statements."""
    company_name: str
    ticker: Optional[str] = None
    fiscal_year: int
    report_type: ReportType
    accounting_standard: AccountingStandard
    currency: Currency = Currency.USD
    
    income_statements: List[IncomeStatement] = Field(default_factory=list)
    balance_sheets: List[BalanceSheet] = Field(default_factory=list)
    cash_flow_statements: List[CashFlowStatement] = Field(default_factory=list)
    
    # Metadata
    filing_date: Optional[date] = None
    source_url: Optional[str] = None
    extraction_date: date = Field(default_factory=date.today)
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_name": "Apple Inc.",
                "ticker": "AAPL",
                "fiscal_year": 2023,
                "report_type": "10-K",
                "accounting_standard": "GAAP",
                "currency": "USD"
            }
        }


class FinancialRatios(BaseModel):
    """Financial ratios and metrics."""
    period: date
    
    # Profitability Ratios
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None
    return_on_invested_capital: Optional[float] = None
    
    # Liquidity Ratios
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    cash_ratio: Optional[float] = None
    
    # Leverage Ratios
    debt_to_equity: Optional[float] = None
    debt_to_assets: Optional[float] = None
    interest_coverage: Optional[float] = None
    
    # Efficiency Ratios
    asset_turnover: Optional[float] = None
    inventory_turnover: Optional[float] = None
    receivables_turnover: Optional[float] = None
    days_sales_outstanding: Optional[float] = None
    days_inventory_outstanding: Optional[float] = None
    days_payable_outstanding: Optional[float] = None
    cash_conversion_cycle: Optional[float] = None
    
    # Valuation Metrics
    price_to_earnings: Optional[float] = None
    price_to_book: Optional[float] = None
    price_to_sales: Optional[float] = None
    ev_to_ebitda: Optional[float] = None


class ForecastAssumptions(BaseModel):
    """Assumptions for financial forecasting and DCF."""
    
    # Revenue Assumptions
    revenue_growth_rate: float = Field(..., description="Annual revenue growth rate")
    revenue_cagr: Optional[float] = None
    
    # Margin Assumptions
    gross_margin: float
    operating_margin: float
    net_margin: Optional[float] = None
    
    # Tax
    tax_rate: float = Field(default=config.defaults.TAX_RATE, description="Effective tax rate")
    
    # CAPEX & Depreciation
    capex_percent_of_revenue: float = Field(default=config.defaults.CAPEX_PERCENT_OF_REVENUE)
    depreciation_percent_of_ppe: float = Field(default=config.defaults.DEPRECIATION_PERCENT_OF_PPE)
    
    # Working Capital
    days_sales_outstanding: int = Field(default=config.defaults.DAYS_SALES_OUTSTANDING)
    days_inventory_outstanding: int = Field(default=config.defaults.DAYS_INVENTORY_OUTSTANDING)
    days_payable_outstanding: int = Field(default=config.defaults.DAYS_PAYABLE_OUTSTANDING)
    dividend_payout_ratio: float = Field(default=0.0, description="Percentage of net income paid as dividends")
    
    # DCF / WACC Specific (NEW)
    risk_free_rate: float = Field(default=config.defaults.RISK_FREE_RATE)
    equity_risk_premium: float = Field(default=config.defaults.EQUITY_RISK_PREMIUM)
    beta: float = Field(default=config.defaults.BETA)
    cost_of_debt: float = Field(default=config.defaults.COST_OF_DEBT)
    terminal_growth_rate: float = Field(default=config.defaults.TERMINAL_GROWTH_RATE)
    wacc: Optional[float] = None
    
    # Scenario
    scenario: str = Field(default="base", description="Forecast scenario: base, bull, bear")



class DCFYearData(BaseModel):
    """Annual data used in DCF calculation."""
    year: int
    ebit: float
    tax_expense: float
    nopat: float
    depreciation_amortization: float
    capex: float
    change_in_nwc: float
    free_cash_flow: float
    discount_factor: float
    pv_of_fcf: float

class DCFValuation(BaseModel):
    """Full DCF Valuation breakdown."""
    forecast_period_fcf: List[DCFYearData]
    sum_pv_fcf: float
    terminal_value: float
    pv_terminal_value: float
    enterprise_value: float
    net_debt: float
    equity_value: float
    shares_outstanding: float
    implied_price_per_share: float
    wacc_used: float
    terminal_growth_used: float

class LinkedModel(BaseModel):
    """Linked 3-statement financial model."""
    company_name: str
    base_year: int
    report_type: ReportType = ReportType.FORM_10K
    forecast_years: int
    accounting_standard: AccountingStandard
    ticker: Optional[str] = None
    
    # Historical Data
    historical_income_statements: List[IncomeStatement]
    historical_balance_sheets: List[BalanceSheet]
    historical_cash_flows: List[CashFlowStatement]
    
    # Forecast Data
    forecast_income_statements: List[IncomeStatement] = Field(default_factory=list)
    forecast_balance_sheets: List[BalanceSheet] = Field(default_factory=list)
    forecast_cash_flows: List[CashFlowStatement] = Field(default_factory=list)
    
    # Assumptions
    assumptions: ForecastAssumptions
    
    # Ratios
    historical_ratios: List[FinancialRatios] = Field(default_factory=list)
    forecast_ratios: List[FinancialRatios] = Field(default_factory=list)
    
    # Validation
    is_balanced: bool = Field(default=False, description="Whether the model balances")
    validation_errors: List[str] = Field(default_factory=list)
    adjustments: List[str] = Field(default_factory=list)
    market_data: Optional[Dict] = Field(None, description="External market data (price, PE, etc.)")
    
    # Investment Logic (NEW)
    recommendation: Optional[str] = Field(None, description="BUY, HOLD, or SELL")
    target_price: Optional[float] = None
    upside_potential: Optional[float] = None
    investment_thesis: Optional[str] = None
    dcf_valuation: Optional[DCFValuation] = None
    ai_summary: Optional[str] = None
    ai_risks: Optional[List[str]] = None
    ai_narrative: Optional[str] = None
    
    # Private / Startup Specific (NEW)
    cap_table: Optional['CapTable'] = None
    reverse_dcf: Optional['ReverseDCFAnalysis'] = None


class FundingRound(BaseModel):
    """Funding round details."""
    name: str = Field(..., description="e.g. Seed, Series A")
    date: date
    pre_money_valuation: float
    amount_raised: float
    post_money_valuation: float
    investors: List[str] = Field(default_factory=list)

class ShareClass(BaseModel):
    """Equity structure."""
    name: str = Field(..., description="Common, Preferred A, etc.")
    shares_issued: float
    price_per_share: Optional[float] = None
    liquidation_preference: float = Field(default=1.0)
    ownership_percentage: Optional[float] = None

class CapTable(BaseModel):
    """Capitalization table."""
    rounds: List[FundingRound] = Field(default_factory=list)
    share_classes: List[ShareClass] = Field(default_factory=list)
    total_fully_diluted_shares: float

class ReverseDCFAnalysis(BaseModel):
    """Reverse DCF outputs."""
    target_price: float
    required_growth_rate: float
    required_margin: float
    years_to_breakeven: Optional[float]
    implied_arr_multiple: Optional[float]
