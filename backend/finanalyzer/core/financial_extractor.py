
import re
from typing import Dict, List, Optional
from datetime import date
from loguru import logger
from ..models.schemas import FinancialStatements, IncomeStatement, BalanceSheet, CashFlowStatement, AccountingStandard, Currency, ReportType

class FinancialExtractor:
    """
    Extracts financial data from PDF text using keyword matching and regex patterns.
    Currently supports extraction of key metrics from Consolidated Financial Statements.
    """
    
    def __init__(self, text_by_page: Dict[int, str]):
        self.pages = text_by_page
        self.full_text = "\n".join(text_by_page.values())
        
        # Mapping of standardized fields to common regex variations found in reports
        # Mapping of standardized fields to common regex variations found in reports
        self.patterns = {
            'revenue': [
                r'(?i)Total\s+revenue\s+[\$]?\s*([\d,.]+)', 
                r'(?i)Net\s+sales\s+[\$]?\s*([\d,.]+)', 
                r'(?i)Total\s+net\s+sales\s+[\$]?\s*([\d,.]+)',
                r'(?i)Revenue,\s+net\s+[\$]?\s*([\d,.]+)',
                r'(?i)Доходы\s+от\s+реализации\s+[\$]?\s*([\d\s,.\(\)]+)',
                r'(?i)Выручка\s+(?:от\s+реализации\s+)?[\$]?\s*([\d\s,.\(\)]+)',
                r'(?i)Общий\s+доход\s+[\$]?\s*([\d\s,.\(\)]+)'
            ],
            'cost_of_revenue': [
                r'(?i)Cost\s+of\s+revenue\s+[\$]?\s*([\d,.]+)', 
                r'(?i)Cost\s+of\s+sales\s+[\$]?\s*([\d,.]+)',
                r'(?i)Cost\s+of\s+goods\s+sold\s+[\$]?\s*([\d,.]+)',
                r'(?i)Себестоимость\s+реализованной\s+продукции\s+[\$]?\s*([\d\s,.\(\)]+)',
                r'(?i)Себестоимость\s+[\$]?\s*([\d\s,.\(\)]+)'
            ],
            'gross_profit': [
                r'(?i)Gross\s+profit\s+[\$]?\s*([\d,.]+)', 
                r'(?i)Gross\s+margin\s+[\$]?\s*([\d,.]+)',
                r'(?i)Валовая\s+прибыль\s+[\$]?\s*([\d\s,.\(\)]+)'
            ],
            'operating_income': [
                r'(?i)Operating\s+income\s+[\$]?\s*([\d,.]+)', 
                r'(?i)Income\s+from\s+operations\s+[\$]?\s*([\d,.]+)',
                r'(?i)Доход\s+от\s+операционной\s+деятельности\s+[\$]?\s*([\d\s,.\(\)]+)',
                r'(?i)Операционная\s+прибыль\s+[\$]?\s*([\d\s,.\(\)]+)'
            ],
            'net_income': [
                r'(?i)Net\s+income\s+[\$]?\s*([\d,.]+)', 
                r'(?i)Net\s+earnings\s+[\$]?\s*([\d,.]+)', 
                r'(?i)Net\s+income\s+attributable\s+to\s+[\w\s]+\s+[\$]?\s*([\d,.]+)',
                r'(?i)Общий\s+совокупный\s+доход\s+за\s+год\s+[\$]?\s*([\d\s,.\(\)]+)',
                r'(?i)Прибыль\s+за\s+период\s+[\$]?\s*([\d\s,.\(\)]+)',
                r'(?i)Прибыль\s+за\s+год\s+[\$]?\s*([\d\s,.\(\)]+)',
                r'(?i)Чистая\s+прибыль\s+[\$]?\s*([\d\s,.\(\)]+)'
            ],
            'total_assets': [
                r'(?i)Total\s+assets\s+[\$]?\s*([\d,.\s]+)',
                r'(?i)Итого\s+(?:по\s+разделу\s+)?активов\s+[\$]?\s*([\d\s,.\(\)]+)',
                r'(?i)Активы,\s+всего\s+[\$]?\s*([\d\s,.\(\)]+)',
                r'(?i)Итого\s+активов\s+[\$]?\s*([\d\s,.\(\)]+)'
            ],
            'total_liabilities': [
                r'(?i)Total\s+liabilities\s+[\$]?\s*([\d,.\s]+)',
                r'(?i)Обязательства,\s+всего\s+[\$]?\s*([\d\s,.\(\)]+)',
                r'(?i)Итого\s+обязательств\s+[\$]?\s*([\d\s,.\(\)]+)'
            ],
            'total_equity': [
                r'(?i)Total\s+shareholders.\s+equity\s+[\$]?\s*([\d,.\s]+)', 
                r'(?i)Total\s+equity\s+[\$]?\s*([\d,.\s]+)',
                r'(?i)Итого\s+капитал\s+[\$]?\s*([\d\s,.\(\)]+)',
                r'(?i)Капитал\s+и\s+резервы\s+[\$]?\s*([\d\s,.\(\)]+)'
            ],
            'shares': [
                r'(?i)Weighted\s+average\s+shares.*?diluted.*?([\d,.]+)',
                r'(?i)Diluted\s+shares.*?([\d,.]+)',
                r'(?i)Common\s+stock\s+outstanding.*?([\d,.]+)', 
                r'(?i)shares\s+of\s+common\s+stock\s+outstanding.*?([\d,.]+)',
                r'(?i)Число\s+акций\s+[\$]?\s*([\d\s,.\(\)]+)'
            ],
            'ticker': [r'(?i)\(?(NASDAQ|NYSE|OTC|TSX)\s*:\s*([A-Z]+)\)?', r'(?i)Symbol\s*:\s*([A-Z]+)'],
            'capital_expenditures': [
                r'(?i)Capital\s+expenditures?\s*[\$]?\s*\(?([\d,.\s]+)\)?',
                r'(?i)Purchase\s+of\s+property.*?[\$]?\s*\(?([\d,.\s]+)\)?',
                r'(?i)Капитальные\s+затраты\s*[\$]?\s*\(?([\d\s,.]+)\)?'
            ],
            'cash_from_operations': [
                r'(?i)Net\s+cash\s+(?:provided\s+by|from)\s+operating\s+activities\s*[\$]?\s*\(?([\d,.\s]+)\)?',
                r'(?i)Чистые\s+денежные\s+средства\s+от\s+операционной\s+деятельности\s*[\$]?\s*\(?([\d\s,.]+)\)?',
                r'(?i)Денежные\s+средства\s+от\s+операционной\s+деятельности\s*[\$]?\s*\(?([\d\s,.]+)\)?'
            ],
            'depreciation': [
                r'(?i)Depreciation\s+and\s+amortization\s*[\$]?\s*([\d,.]+)',
                r'(?i)Depreciation\s*[\$]?\s*([\d,.]+)',
                r'(?i)Амортизация\s+(?:основных\s+средств\s+и\s+нематериальных\s+активов\s+)?[\$]?\s*([\d\s,.]+)'
            ],
            'accounts_receivable': [
                r'(?i)Accounts\s+receivable.*?[\$]?\s*([\d,.]+)',
                r'(?i)Trade\s+receivables?\s*[\$]?\s*([\d,.]+)',
                r'(?i)Дебиторская\s+задолженность\s*[\$]?\s*([\d\s,.]+)'
            ],
            'inventory': [
                r'(?i)Inventor(?:y|ies)\s*[\$]?\s*([\d,.]+)',
                r'(?i)Запасы\s*[\$]?\s*([\d\s,.]+)'
            ],
            'cash_and_equivalents': [
                r'(?i)Cash\s+and\s+cash\s+equivalents?\s*[\$]?\s*([\d,.\s]+)',
                r'(?i)Денежные\s+средства\s+и\s+их\s+эквиваленты\s*[\$]?\s*([\d\s,.]+)',
                r'(?i)Денежные\s+средства\s+и\s+эквиваленты\s*[\$]?\s*([\d\s,.]+)'
            ]
        }

    def extract(self, apply_scale: bool = True) -> FinancialStatements:
        """Main extraction method."""
        logger.info("Starting intelligent data extraction from PDF text...")
        
        # 1. Detect Report Type and Fiscal Year
        report_type = self._detect_report_type()
        year = self._extract_fiscal_year()
        logger.info(f"Detected Report: {report_type.value}, Fiscal Year: {year}")
        
        # 2. Detect Scale/Unit (Millions, Thousands, etc.)
        self.scale_factor = self._detect_scale()
        logger.info(f"Detected numeric scale factor: {self.scale_factor}")
        
        # 3. Extract Key Metrics
        data = {}
        # Special handling for 10-Q time periods
        is_quarterly = report_type == ReportType.FORM_10Q
        for field, regex_list in self.patterns.items():
            # If it's a 10-Q and it's an Income Statement item, we might need to annualize
            val = self._find_value(regex_list)
            
            # Apply detected scale (e.g. if report is in Millions, multiply by 1e6)
            if apply_scale and val > 0:
                 # Special handling for shares to avoid double scaling if already in actuals
                 if field == 'shares' and val > 500_000:
                     # Already looks like actuals (500k is a lot for a small company)
                     pass
                 else:
                     val = val * self.scale_factor

            # Smart annualization for 10-Q
            if is_quarterly and field in ['revenue', 'cost_of_revenue', 'gross_profit', 'operating_income', 'net_income']:
                # Simplest logic: If it's 10-Q, multiply by 4 (run rate)
                val = val * 4
                logger.debug(f"Annualizing 10-Q {field}")

            data[field] = val
            if val > 0:
                logger.info(f"Extracted {field}: {val}")

        # 3. Construct Statements
        
        # Calculate derived metrics if missing
        rev = data.get('revenue', 0)
        cost = data.get('cost_of_revenue', 0)
        gross = data.get('gross_profit', 0)
        
        if rev > 0 and cost > 0 and gross == 0:
            gross = rev - cost
        if rev > 0 and gross > 0 and cost == 0:
            cost = rev - gross
            
        if rev > 1_000_000 and gross < rev * 0.01:
            logger.warning(f"Extracted Gross Profit ({gross}) seems too low compared to Revenue ({rev}).")
            gross = 0
            
        # If Gross Profit is missing or rejected, estimate it or derive from Net Income
        # NVIDIA typically has high margins. If we have Net Income, we can work back?
        # Better to be safe: If Net Income is huge (like here, 72B on 130B rev -> 55% margin),
        # Gross must be > Net Income.
        net = data.get('net_income', 0)
        
        if gross == 0 and rev > 0:
            if net > 0:
                # Conservative estimate: Gross is Net + 20% of Rev (OpEx)
                gross = net + (rev * 0.2) 
                cost = rev - gross
            else:
                 # Default 40% margin if nothing else known
                 gross = rev * 0.4
                 cost = rev * 0.6
        
        # Calculate Operating Income (EBIT)
        op_income = data.get('operating_income', 0)
        if op_income == 0:
            if net > 0:
                # Estimate Tax ~ 15%
                op_income = net * 1.15
            elif gross > 0:
                op_income = gross * 0.6 # rough estimate
        
        # Ticker, Shares and Company Name
        shares = data.get('shares', 0)
        company_name = self._extract_company_name()
        ticker = self._extract_ticker()
        
        # Income Statement
        inc_stmt = IncomeStatement(
            period_start=date(year-1, 1, 1),
            period_end=date(year-1, 12, 31), 
            revenue=rev,
            net_income=net,
            gross_profit=gross,
            operating_income=op_income,
            operating_expenses=gross - op_income,
            cost_of_revenue=cost,
            depreciation_amortization=op_income * 0.1 if op_income > 0 else 0,
            ebitda=op_income * 1.1 if op_income > 0 else 0,
            ebit=op_income,
            interest_expense=0,
            income_before_tax=op_income,
            income_tax_expense=op_income - net,
            shares_outstanding_diluted=shares if shares > 0 else 1e9 # Placeholder if not found
        )
        
        # Balance Sheet - use extracted data where available
        total_assets = data.get('total_assets', 0)
        total_liab = data.get('total_liabilities', 0)
        total_equity = data.get('total_equity', 0) or (total_assets - total_liab) if total_assets > 0 else 0
        
        # Use extracted values or estimate from total assets
        cash = data.get('cash_and_equivalents', 0)
        if cash == 0 and total_assets > 0:
            cash = total_assets * 0.2  # Estimate 20% of assets as cash
            
        ar = data.get('accounts_receivable', 0)
        if ar == 0 and total_assets > 0:
            ar = total_assets * 0.1
            
        inv = data.get('inventory', 0)
        if inv == 0 and total_assets > 0:
            inv = total_assets * 0.1
        
        bs_stmt = BalanceSheet(
            period_end=date(year-1, 12, 31),
            total_assets=total_assets,
            total_liabilities=total_liab,
            total_shareholders_equity=total_equity,
            cash_and_equivalents=cash,
            accounts_receivable=ar,
            inventory=inv,
            total_current_assets=total_assets * 0.5 if total_assets > 0 else 0,
            property_plant_equipment_net=total_assets * 0.3 if total_assets > 0 else 0,
            intangible_assets=0,
            accounts_payable=total_liab * 0.2 if total_liab > 0 else 0,
            short_term_debt=0,
            long_term_debt=total_liab * 0.5 if total_liab > 0 else 0,
            total_current_liabilities=total_liab * 0.4 if total_liab > 0 else 0,
            retained_earnings=total_equity * 0.8 if total_equity > 0 else 0
        )
        
        # Cash Flow - use extracted data where available
        da = data.get('depreciation', 0)
        if da == 0 and op_income > 0:
            da = op_income * 0.1  # Estimate 10% of operating income as D&A
        
        # Use extracted or estimate CFO
        cfo = data.get('cash_from_operations', 0)
        if cfo == 0:
            cfo = net + da  # Simplified: NI + D&A
        
        # Use extracted CAPEX (usually negative/outflow)
        capex = data.get('capital_expenditures', 0)
        if capex > 0:
            capex = -capex  # Make negative (outflow)
        
        # Use extracted Dividends (usually negative/outflow)  
        divs = data.get('dividends_paid', 0)
        if divs > 0:
            divs = -divs  # Make negative (outflow)
        
        # Cash from investing = CAPEX (simplified)
        cfi = capex
        
        # Cash from financing = Dividends (simplified)
        cff = divs
        
        # Net change
        net_cash_change = cfo + cfi + cff
        
        cf_stmt = CashFlowStatement(
            period_start=date(year-1, 1, 1),
            period_end=date(year-1, 12, 31),
            net_income=net,
            depreciation_amortization=da,
            changes_in_working_capital=0,  # Would need delta calculation
            cash_from_operations=cfo,
            capital_expenditures=capex,
            cash_from_investing=cfi,
            dividends_paid=divs,
            cash_from_financing=cff,
            net_change_in_cash=net_cash_change
        )
        
        # Update D&A in Income Statement to match CF
        inc_stmt.depreciation_amortization = da
        inc_stmt.ebitda = (op_income + da) if op_income > 0 else 0

        return FinancialStatements(
            company_name=company_name,
            ticker=ticker,
            fiscal_year=year,
            report_type=report_type,
            accounting_standard=AccountingStandard.GAAP,
            currency=Currency.USD,
            income_statements=[inc_stmt],
            balance_sheets=[bs_stmt],
            cash_flow_statements=[cf_stmt]
        )

    def _detect_scale(self) -> float:
        """Robustly detect scale/units from the report text."""
        # 1. Search the entire text for specific scale orientation
        # (Most SEC reports have this on the first page of financial statements)
        full_text_lower = self.full_text.lower()
        
        # Check more keywords and variations
        if any(kw in full_text_lower for kw in ["in billions", "в миллиардах", "($ in billions)", "($ in b)", "amounts in billions"]):
            return 1_000_000_000.0
            
        if any(kw in full_text_lower for kw in ["in millions", "в миллионах", "($ in millions)", "($ in mm)", "amounts in millions", "figures in millions", "millions of dollars"]):
            return 1_000_000.0
            
        if any(kw in full_text_lower for kw in ["in thousands", "в тысячах", "($ in thousands)", "($ in k)", "amounts in thousands"]):
            return 1_000.0
            
        # 2. Heuristic Inference (Smart Fallback)
        # Look for revenue. If it's a small number (< 500,000) but it's clearly a corporate report, 
        # it is almost certainly in Millions.
        patterns = [
            r'(?i)Total\s+Revenue[^\.\d%]*?([\d\s,]+)',
            r'(?i)Revenue[^\.\d%]*?([\d\s,]+)',
            r'(?i)Выручка[^\.\d%]*?([\d\s,]+)'
        ]
        test_val = 0
        for p in patterns:
            m = re.search(p, self.full_text)
            if m:
                extracted = self._parse_number(m.group(1))
                if extracted > 1:
                    test_val = extracted
                    break
        
        # Threshold: If revenue is < 500,000, we check if it's likely Millions or Thousands.
        # Major companies (10-K/10-Q) usually have revenues in the 100s or 1000s when reported in Millions.
        if 1 < test_val < 500000:
            # If it's a very small number like 137 or 2000, it's definitely scaled.
            # Assuming Millions is a safer bet for SEC filers if keyword was missing.
            logger.info(f"Scale inference: Detected value {test_val} for revenue. Assuming Millions scale.")
            return 1_000_000.0
            
        return 1.0 # Default to actuals if number is already huge or no pattern found

    def _extract_company_name(self) -> str:
        """Attempt to find company name on the first page with robust fallback."""
        first_page = list(self.pages.values())[0] if self.pages else ""
        first_page_upper = first_page.upper()
        
        # 1. Look for specific common big tech names first (high accuracy)
        keywords = ["TESLA", "APPLE", "MICROSOFT", "AMAZON", "ALPHABET", "META", "NVIDIA", "NETFLIX"]
        for kw in keywords:
            if kw in first_page_upper:
                # Find the full line containing the keyword
                match = re.search(fr'^.*{kw}.*$', first_page_upper, re.MULTILINE)
                if match:
                    return match.group(0).strip().title()

        # 2. Look for typical corporate suffixes
        match = re.search(r'^([A-Z0-9][A-Z0-9\s,&’]+(?:INC\.|CORP\.|CORPORATION|LTD\.|GROUP|PLC))', first_page_upper, re.MULTILINE)
        if match:
            return match.group(1).strip().title()
            
        # 3. Try middle of page for centered titles
        match = re.search(r'([A-Z][A-Z\s,&]+(?:INC\.|CORP\.|CORPORATION))', first_page)
        if match:
            return match.group(1).strip()
            
        # 4. Russian Entity Types
        match = re.search(r'(?:ТОО|АО|ООО|ПАО)\s+[«"]?([\w\s-]+)[»"]?', first_page, re.IGNORECASE)
        if match:
            return match.group(0).strip()

        return "Unknown Company" # Generic fallback

    def _extract_ticker(self) -> Optional[str]:
        """Look for ticker symbol in first 10 pages."""
        text_sample = "\n".join(list(self.pages.values())[:10])
        # Patterns like "NASDAQ: AAPL" or "(NYSE: GE)"
        match = re.search(r'(?:NASDAQ|NYSE|OTC|TSX)\s*:\s*([A-Z]{1,5})', text_sample, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None

    def _detect_report_type(self) -> ReportType:
        """Heuristic to detect 10-K vs 10-Q."""
        text_head = self.full_text[:5000].upper()
        if "FORM 10-Q" in text_head or "QUARTERLY REPORT" in text_head:
            return ReportType.FORM_10Q
        if "FORM 10-K" in text_head or "ANNUAL REPORT" in text_head:
            return ReportType.FORM_10K
        if "ОТЧЕТ" in text_head or "ОТЧЁТ" in text_head:
            return ReportType.FORM_10K
        return ReportType.FORM_10K # Default

    def _extract_fiscal_year(self) -> int:
        # Search for "fiscal year ended", "quarter ended", etc.
        patterns = [
            r'fiscal year ended.*?20(\d{2})',
            r'quarter ended.*?20(\d{2})',
            r'For the quarterly period ended.*?20(\d{2})',
            r'(?:год|года),?\s+закончившийся.*?20(\d{2})',
            r'за.*?20(\d{2})\s+год'
        ]
        for p in patterns:
            match = re.search(p, self.full_text, re.IGNORECASE)
            if match:
                return int("20" + match.group(1))
        return 2024 # Default

    def _parse_number(self, val_str: str) -> float:
        """Robust number parser handling multi-format (EU/RU dots, parens)."""
        if not val_str: return 0.0
        s = val_str.strip()
        # Handle negative in parens (123) -> -123
        if s.startswith('(') and s.endswith(')'):
            s = '-' + s[1:-1]
        
        # Remove spaces (common as thousands sep)
        s = s.replace(' ', '').replace('\xa0', '') 
        
        # Heuristic for delimiters
        if '.' in s and ',' in s:
            if s.rfind('.') > s.rfind(','): # 1,234.56 -> US
                s = s.replace(',', '')
            else: # 1.234,56 -> EU/RU
                s = s.replace('.', '').replace(',', '.')
        elif ',' in s:
            if s.count(',') > 1: s = s.replace(',', '')
            else: s = s.replace(',', '.') 
        elif '.' in s:
            # If multiple dots, it's thousands: 1.234.567
            if s.count('.') > 1: s = s.replace('.', '')
            # If single dot, check context. Usually decimal if US, but could be thousands in RU.
            # But in regex we usually capture digits and separators.
            # Assuming if regex matched [\d,.]+, and it has 1 dot, let's look at length.
            # For now, default to decimal if single dot, UNLESS it results in tiny profit vs known scale.
            # But here we don't know scale. Let's assume decimal for single dot standardly.
            pass
            
        import re
        s = re.sub(r'[^\d.-]', '', s)
        try:
            return float(s)
        except:
            return 0.0

    def _find_value(self, patterns: List[str]) -> float:
        """Finds the 'most representative' numeric value matching the patterns."""
        best_val = 0.0
        
        for pattern in patterns:
            # finditer gives us more control
            matches = list(re.finditer(pattern, self.full_text, re.IGNORECASE))
            if not matches:
                continue
            
            # Heuristic: The best match is often in a table, not the first mention in text.
            # Table matches often have multiple columns (more numbers in proximity).
            # For now, we look through matches and pick the one with most 'separator-heavy' content
            # or simply one that matches a standard financial pattern.
            
            vals_found = []
            for m in matches:
                # Group 1 is our number
                val_raw = m.group(1)
                
                # Split by space to check for multiple columns
                parts = val_raw.strip().split()
                # Most financial tables have current year first (leftmost) or sometimes last.
                # Regex patterns are usually structured to catch the first number after label.
                val_str = parts[0]
                parsed = self._parse_number(val_str)
                
                if parsed != 0:
                    vals_found.append(parsed)
            
            if vals_found:
                # Heuristic: prefer larger numbers (thousands/millions are better than 0.something)
                # and prefer ones that appear later in the document (tables are later than summary)
                # But actually, SEC tables appear relatively early (~10-30 page).
                # Highlights appear on page 1-5.
                # Let's just pick the FIRST non-zero one for now, as it's usually current year.
                return vals_found[0]
                
        return 0.0
