"""
Custom Exceptions for Financial Analyzer.

Define application-specific exceptions for better error handling and debugging.
"""


class FinancialAnalyzerError(Exception):
    """Base exception for all Financial Analyzer errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# =============================================================================
# DATA EXTRACTION ERRORS
# =============================================================================

class ExtractionError(FinancialAnalyzerError):
    """Error during data extraction from PDF or other sources."""
    pass


class PDFParseError(ExtractionError):
    """Failed to parse PDF file."""
    pass


class OCRError(ExtractionError):
    """OCR processing failed."""
    pass


class TableExtractionError(ExtractionError):
    """Failed to extract tables from document."""
    pass


# =============================================================================
# VALIDATION ERRORS
# =============================================================================

class ValidationError(FinancialAnalyzerError):
    """Data validation failed."""
    pass


class BalanceSheetImbalanceError(ValidationError):
    """Balance sheet does not balance (Assets != Liabilities + Equity)."""
    
    def __init__(self, difference: float, period: str):
        super().__init__(
            f"Balance sheet imbalance of ${difference:,.0f} for period {period}",
            {"difference": difference, "period": period}
        )


class MissingDataError(ValidationError):
    """Required data is missing."""
    
    def __init__(self, field_name: str, context: str = ""):
        super().__init__(
            f"Missing required field: {field_name}" + (f" ({context})" if context else ""),
            {"field": field_name, "context": context}
        )


# =============================================================================
# FORECAST ERRORS
# =============================================================================

class ForecastError(FinancialAnalyzerError):
    """Error during financial forecasting."""
    pass


class InsufficientHistoricalDataError(ForecastError):
    """Not enough historical data for forecasting."""
    
    def __init__(self, required: int, available: int):
        super().__init__(
            f"Insufficient historical data: need {required}, have {available}",
            {"required": required, "available": available}
        )


class InvalidAssumptionsError(ForecastError):
    """Forecast assumptions are invalid or out of range."""
    pass


# =============================================================================
# VALUATION ERRORS
# =============================================================================

class ValuationError(FinancialAnalyzerError):
    """Error in valuation calculations."""
    pass


class NegativeValuationError(ValuationError):
    """Calculated a negative valuation (equity value < 0)."""
    
    def __init__(self, equity_value: float):
        super().__init__(
            f"Calculated negative equity value: ${equity_value:,.0f}",
            {"equity_value": equity_value}
        )


class WACCCalculationError(ValuationError):
    """Failed to calculate WACC."""
    pass


# =============================================================================
# EXTERNAL API ERRORS
# =============================================================================

class ExternalAPIError(FinancialAnalyzerError):
    """Error from external API (Yahoo Finance, HuggingFace, etc.)."""
    pass


class MarketDataError(ExternalAPIError):
    """Failed to fetch market data."""
    
    def __init__(self, ticker: str, source: str = "Yahoo Finance"):
        super().__init__(
            f"Failed to fetch market data for {ticker} from {source}",
            {"ticker": ticker, "source": source}
        )


class RateLimitError(ExternalAPIError):
    """API rate limit exceeded."""
    pass


# =============================================================================
# REPORT GENERATION ERRORS
# =============================================================================

class ReportGenerationError(FinancialAnalyzerError):
    """Error generating PDF report."""
    pass


class ChartGenerationError(ReportGenerationError):
    """Failed to generate chart/visualization."""
    pass
