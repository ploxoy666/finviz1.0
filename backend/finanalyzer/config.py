"""
Centralized Configuration Management.

All application settings, constants, and environment variables are managed here.
This follows the 12-factor app methodology for configuration.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# =============================================================================
# ENVIRONMENT DETECTION
# =============================================================================

def is_streamlit_cloud() -> bool:
    """Detect if running on Streamlit Cloud (limited resources)."""
    return (
        os.environ.get("STREAMLIT_RUNTIME_ENV") == "cloud" or 
        os.environ.get("HOSTNAME", "").startswith("streamlit")
    )


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return os.environ.get("DEBUG", "").lower() in ("true", "1", "yes")


# =============================================================================
# ENUMS FOR TYPE SAFETY
# =============================================================================

class Recommendation(str, Enum):
    """Investment recommendation types."""
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"


class AnalysisMode(str, Enum):
    """Application analysis modes."""
    QUICK_PULSE = "Quick Market Pulse"
    DEEP_REPORT = "Deep Report Intelligence"
    STARTUP_VALUATOR = "Private / Startup Valuator"


class ScenarioType(str, Enum):
    """Forecast scenario types."""
    BASE = "base"
    BULL = "bull"
    BEAR = "bear"


# =============================================================================
# DEFAULT VALUES (Magic Numbers centralized)
# =============================================================================

@dataclass(frozen=True)
class DefaultMetrics:
    """Default values for financial metrics when data is unavailable."""
    
    # Margins
    GROSS_MARGIN: float = 0.40
    OPERATING_MARGIN: float = 0.20
    NET_MARGIN: float = 0.10
    
    # Growth
    REVENUE_GROWTH_RATE: float = 0.05
    
    # Valuation
    TAX_RATE: float = 0.21
    RISK_FREE_RATE: float = 0.04
    EQUITY_RISK_PREMIUM: float = 0.055
    TERMINAL_GROWTH_RATE: float = 0.025
    BETA: float = 1.0
    COST_OF_DEBT: float = 0.05
    
    # Working Capital Days
    DAYS_SALES_OUTSTANDING: int = 45
    DAYS_INVENTORY_OUTSTANDING: int = 60
    DAYS_PAYABLE_OUTSTANDING: int = 30
    
    # CAPEX
    CAPEX_PERCENT_OF_REVENUE: float = 0.05
    DEPRECIATION_PERCENT_OF_PPE: float = 0.10
    
    # Fallbacks for missing data
    FALLBACK_SHARES_OUTSTANDING: float = 1e9  # 1 billion shares
    

@dataclass(frozen=True)
class Thresholds:
    """Validation thresholds and tolerances."""
    
    # Balance Sheet
    BALANCE_TOLERANCE: float = 1000.0  # $1000 tolerance for rounding
    
    # Margins (clamps)
    MIN_GROSS_MARGIN: float = 0.10
    MAX_GROSS_MARGIN: float = 0.95
    MIN_OPERATING_MARGIN: float = -0.50  # Allow negative for growth companies
    MAX_OPERATING_MARGIN: float = 0.80
    
    # CAPEX
    MIN_CAPEX_PERCENT: float = 0.01
    MAX_CAPEX_PERCENT: float = 0.20
    
    # Valuation sanity checks
    MAX_REASONABLE_STOCK_PRICE: float = 10000.0
    
    # Unit detection
    SHARES_MILLIONS_THRESHOLD: float = 1e6


@dataclass(frozen=True)
class ScoringWeights:
    """Weights for investment recommendation scoring."""
    
    # Growth points
    HIGH_GROWTH_THRESHOLD: float = 0.15
    MEDIUM_GROWTH_THRESHOLD: float = 0.08
    LOW_GROWTH_THRESHOLD: float = 0.03
    HIGH_GROWTH_POINTS: int = 3
    MEDIUM_GROWTH_POINTS: int = 2
    LOW_GROWTH_POINTS: int = 1
    
    # Margin points
    HIGH_MARGIN_THRESHOLD: float = 0.20
    MEDIUM_MARGIN_THRESHOLD: float = 0.10
    LOW_MARGIN_THRESHOLD: float = 0.05
    
    # Valuation upside
    HIGH_UPSIDE_THRESHOLD: float = 0.40
    MEDIUM_UPSIDE_THRESHOLD: float = 0.20
    LOW_UPSIDE_THRESHOLD: float = 0.05
    
    # Score thresholds for recommendation
    BUY_THRESHOLD: int = 6
    HOLD_THRESHOLD: int = 3


# =============================================================================
# API CONFIGURATION
# =============================================================================

@dataclass
class APIConfig:
    """External API configuration."""
    
    # Hugging Face
    HF_API_KEY: Optional[str] = field(
        default_factory=lambda: os.environ.get("HF_TOKEN")
    )
    
    # Yahoo Finance
    YFINANCE_TIMEOUT: int = 10
    YFINANCE_USER_AGENT: str = "Mozilla/5.0 (compatible; FinancialAnalyzer/1.0)"
    
    # Rate limiting
    REQUEST_DELAY_SECONDS: float = 0.5


@dataclass
class PDFConfig:
    """PDF parsing configuration."""
    
    # OCR settings
    OCR_DPI: int = 300
    OCR_LANGUAGE: str = "eng"
    
    # Page limits
    MAX_PAGES_FOR_TABLES: int = 20
    MAX_PAGES_FOR_SENTIMENT: int = 5
    
    # Text extraction
    MIN_TEXT_LENGTH_FOR_DIGITAL: int = 100


@dataclass
class ReportConfig:
    """PDF report generation configuration."""
    
    # Page size (US Letter in landscape)
    PAGE_WIDTH: float = 11.0  # inches
    PAGE_HEIGHT: float = 8.5  # inches
    
    # Margins
    LEFT_MARGIN: float = 0.5
    RIGHT_MARGIN: float = 0.5
    TOP_MARGIN: float = 0.5
    BOTTOM_MARGIN: float = 0.5
    
    # Colors (hex)
    PRIMARY_COLOR: str = "#1f4788"
    SECONDARY_COLOR: str = "#2d5aa0"
    ACCENT_COLOR: str = "#10b981"
    WARNING_COLOR: str = "#f59e0b"
    DANGER_COLOR: str = "#ef4444"
    LIGHT_GREY: str = "#f0f2f5"


# =============================================================================
# SINGLETON CONFIG INSTANCE
# =============================================================================

@dataclass
class AppConfig:
    """Main application configuration container."""
    
    # Runtime environment
    IS_STREAMLIT_CLOUD: bool = field(default_factory=is_streamlit_cloud)
    DEBUG: bool = field(default_factory=is_debug_mode)
    
    # Sub-configurations
    defaults: DefaultMetrics = field(default_factory=DefaultMetrics)
    thresholds: Thresholds = field(default_factory=Thresholds)
    scoring: ScoringWeights = field(default_factory=ScoringWeights)
    api: APIConfig = field(default_factory=APIConfig)
    pdf: PDFConfig = field(default_factory=PDFConfig)
    report: ReportConfig = field(default_factory=ReportConfig)
    
    # Application info
    APP_NAME: str = "Financial Alpha Intelligence"
    APP_VERSION: str = "1.0.0"
    

# Global config instance
config = AppConfig()


# =============================================================================
# PEER MAPPINGS (for Market Pulse mode)
# =============================================================================

SECTOR_PEERS = {
    # Tech
    "AAPL": ["MSFT", "GOOGL", "AMZN", "META"],
    "MSFT": ["AAPL", "GOOGL", "AMZN", "ORCL"],
    "GOOGL": ["META", "MSFT", "AMZN", "AAPL"],
    "NVDA": ["AMD", "INTC", "TSM", "AVGO"],
    "AMD": ["NVDA", "INTC", "TSM", "QCOM"],
    
    # Automotive
    "TSLA": ["F", "GM", "RIVN", "LCID", "NIO"],
    
    # Finance
    "JPM": ["BAC", "GS", "MS", "C"],
    "GS": ["MS", "JPM", "BAC", "C"],
    
    # Retail
    "AMZN": ["WMT", "TGT", "COST", "EBAY"],
    "WMT": ["TGT", "COST", "KR", "AMZN"],
}


def get_peers(ticker: str) -> list:
    """Get peer companies for a given ticker."""
    return SECTOR_PEERS.get(ticker.upper(), [])
