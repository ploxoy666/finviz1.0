"""
Financial Report Analyzer Package.

AI-powered financial report analyzer with 3-statement modeling and DCF valuation.
"""

__version__ = "1.0.0"
__author__ = "Financial Modeling Team"
__description__ = "AI-powered financial report analyzer with 3-statement modeling"

# Core configuration
from .config import config, Recommendation, AnalysisMode, ScenarioType

# Custom exceptions
from .exceptions import (
    FinancialAnalyzerError,
    ExtractionError,
    ValidationError,
    ForecastError,
    ValuationError,
    ExternalAPIError,
    ReportGenerationError,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    
    # Config
    "config",
    "Recommendation",
    "AnalysisMode",
    "ScenarioType",
    
    # Exceptions
    "FinancialAnalyzerError",
    "ExtractionError",
    "ValidationError", 
    "ForecastError",
    "ValuationError",
    "ExternalAPIError",
    "ReportGenerationError",
]
