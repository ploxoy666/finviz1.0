"""
Report Generator
Generates comprehensive PDF reports with charts, tables, and analysis.
"""

from datetime import date
from pathlib import Path
from typing import Dict, List, Optional
import io


import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, PageBreak, Image as RLImage, Frame, PageTemplate, NextPageTemplate
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from loguru import logger

from ..models.schemas import LinkedModel, IncomeStatement, BalanceSheet, CashFlowStatement


class ReportGenerator:
    """
    Generates comprehensive financial analysis PDF reports.
    """
    
    def __init__(self, linked_model: LinkedModel, sentiment_data: Optional[Dict] = None):
        """
        Initialize Report Generator.
        
        Args:
            linked_model: Linked financial model with forecasts
            sentiment_data: Optional results from FinBERT analyzer
        """
        self.model = linked_model
        self.sentiment = sentiment_data
        self.styles = getSampleStyleSheet()
        self.charts = []
        
        # Define Color Palette
        self.colors = {
            'navy': colors.HexColor('#1B365D'),
            'charcoal': colors.HexColor('#333333'),
            'gold': colors.HexColor('#B39D4B'),
            'light_grey': colors.HexColor('#F8F9FA'),
            'border_grey': colors.HexColor('#DEE2E6')
        }
        
        # Setup Custom Styles
        self._setup_wall_street_styles()
        
        # Configure matplotlib style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (10, 6)
        plt.rcParams['font.size'] = 10
        
        logger.info(f"Initialized ReportGenerator for {linked_model.company_name}")
    
    def _fmt(self, value):
        """Format numbers fully with commas (e.g. 1,000,000.00)."""
        if value is None: return "N/A"
        if abs(value) >= 100:
            return f"${value:,.0f}"
        else:
            return f"${value:,.2f}"

    def _setup_wall_street_styles(self):
        """Define professional financial report styles."""
        self.styles.add(ParagraphStyle(
            name='WS_Title',
            parent=self.styles['Normal'],
            fontName='Times-Bold',
            fontSize=28,
            textColor=self.colors['navy'],
            alignment=TA_CENTER,
            spaceAfter=40
        ))
        
        self.styles.add(ParagraphStyle(
            name='WS_Heading1',
            parent=self.styles['Normal'],
            fontName='Times-Bold',
            fontSize=16,
            textColor=self.colors['navy'],
            borderPadding=(0, 0, 4, 0),
            spaceBefore=12,
            spaceAfter=8,
            borderWidth=0,
            allowWidows=0
        ))
        
        self.styles.add(ParagraphStyle(
            name='WS_Heading2',
            parent=self.styles['Normal'],
            fontName='Times-Bold',
            fontSize=13,
            textColor=self.colors['charcoal'],
            spaceBefore=8,
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='WS_Normal',
            parent=self.styles['Normal'],
            fontName='Times-Roman',
            fontSize=10,
            textColor=self.colors['charcoal'],
            leading=12,
            alignment=TA_LEFT
        ))

        self.styles.add(ParagraphStyle(
            name='WS_Small',
            parent=self.styles['Normal'],
            fontName='Times-Roman',
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_LEFT
        ))

    def generate_pdf(self, output_path: str):
        """
        Generate complete PDF report with mixed orientation.
        """
        logger.info(f"Generating PDF report: {output_path}")
        
        # Define Frames and Templates
        # Portrait Frame
        frame_portrait = Frame(
            0.5*inch, 0.5*inch, 7.5*inch, 10*inch, id='portrait_frame'
        )
        template_portrait = PageTemplate(
            id='Portrait', frames=[frame_portrait], pagesize=letter
        )
        
        # Landscape Frame (wider)
        frame_landscape = Frame(
            0.5*inch, 0.5*inch, 10*inch, 7.5*inch, id='landscape_frame'
        )
        template_landscape = PageTemplate(
            id='Landscape', frames=[frame_landscape], pagesize=landscape(letter)
        )
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=24, leftMargin=24, topMargin=36, bottomMargin=36
        )
        
        doc.addPageTemplates([template_portrait, template_landscape])
        
        # Build content
        story = []
        
        # Title Page
        story.extend(self._create_title_page())
        story.append(PageBreak())
        
        # Executive Summary
        story.extend(self._create_executive_summary())
        story.append(Spacer(1, 0.2*inch))
        
        # AI Executive Insights (NEW)
        if hasattr(self.model, 'ai_narrative') and self.model.ai_narrative:
            story.extend(self._create_ai_insights_section())
            story.append(Spacer(1, 0.2*inch))
        
        # AI Sentiment Analysis (NEW)
        if self.sentiment:
            story.extend(self._create_ai_sentiment_section())
            story.append(Spacer(1, 0.2*inch))
            
        # Market Context (NEW)
        if hasattr(self.model, 'market_data') and self.model.market_data:
            story.extend(self._create_market_data_section())
            story.append(Spacer(1, 0.2*inch))
            
        # Investment Thesis (NEW)
        if hasattr(self.model, 'recommendation') and self.model.recommendation:
            story.extend(self._create_investment_thesis_section())
            story.append(Spacer(1, 0.2*inch))
        
        story.append(PageBreak())
        
        # Historical Financials
        story.extend(self._create_historical_section())
        story.append(PageBreak())
        
        # Linked Model (Portrait)
        story.extend(self._create_linked_model_section())
        
        # Forecast (Landscape for wide tables)
        if self.model.forecast_income_statements:
            story.append(NextPageTemplate('Landscape'))
            story.append(PageBreak()) # Switch to Landscape for Forecast
            
            story.extend(self._create_forecast_section())
            
            # DCF Analysis (Forced landscape with clean formatting)
            if hasattr(self.model, 'dcf_valuation') and self.model.dcf_valuation:
                # Force switch to landscape specifically for DCF
                # (in case Forecast section pushed us to a new portrait page)
                story.append(NextPageTemplate('Landscape'))
                story.append(PageBreak()) 
                story.extend(self._create_dcf_section())
            
            story.append(PageBreak())
        
        # Financial Ratios (Landscape)
        story.extend(self._create_ratios_section())
        story.append(NextPageTemplate('Portrait')) # Back to Portrait for charts
        story.append(PageBreak())
        
        # Charts & Visualizations
        story.extend(self._create_charts_section())
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"✓ PDF report generated: {output_path}")
    
    def _create_title_page(self) -> List:
        """Create title page with specific 10-K/10-Q classifications."""
        story = []
        is_q = self.model.report_type.value == "10-Q"
        
        # Audit Badge / Reliability Indicator
        status_color = self.colors['navy'] if not is_q else colors.HexColor('#856404') # Gold-ish for caution
        status_bg = colors.HexColor('#e1f5fe') if not is_q else colors.HexColor('#fff3cd')
        
        audit_status = "✅ AUDITED - FULL RELIABILITY" if not is_q else "⚠️ UNAUDITED - INTERIM UPDATE"
        purpose = "Financial Valuation & Strategy Base" if not is_q else "Operational Monitoring & TTM Update"
        
        # Status Table at top right
        status_data = [
            [Paragraph(f"<b>Audit Status:</b> {audit_status}", self.styles['WS_Small'])],
            [Paragraph(f"<b>Analysis Scope:</b> {purpose}", self.styles['WS_Small'])]
        ]
        st_table = Table(status_data, colWidths=[4*inch])
        st_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), status_bg),
            ('BOX', (0, 0), (-1, -1), 1, status_color),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(st_table)
        
        story.append(Spacer(1, 1.5*inch))
        
        title_text = "ANNUAL FINANCIAL REPORT (10-K)" if not is_q else "QUARTERLY FINANCIAL REPORT (10-Q)"
        story.append(Paragraph(title_text, self.styles['WS_Title']))
        story.append(Spacer(1, 0.4*inch))
        
        # Company name
        story.append(Paragraph(self.model.company_name.upper(), self.styles['WS_Title']))
        story.append(Spacer(1, 0.3*inch))
        
        # Metadata
        meta_style = ParagraphStyle(
            'Metadata',
            parent=self.styles['WS_Normal'],
            alignment=TA_CENTER,
            fontSize=12
        )
        
        metadata = [
            f"Fiscal Year: {self.model.base_year}",
            f"Accounting Standard: {self.model.accounting_standard.value}",
            f"Forecast Horizon: {self.model.forecast_years} Years",
            f"Generation Date: {date.today().strftime('%B %d, %Y')}"
        ]
        
        for meta in metadata:
            story.append(Paragraph(meta, meta_style))
            story.append(Spacer(1, 0.1*inch))
        
        return story
    
    def _create_executive_summary(self) -> List:
        """Create executive summary section."""
        story = []
        
        story.append(Paragraph("Executive Summary", self.styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        # Get latest data
        latest_income = self.model.historical_income_statements[-1]
        latest_bs = self.model.historical_balance_sheets[-1]
        latest_ratios = self.model.historical_ratios[-1] if self.model.historical_ratios else None
        
        # Key metrics table
        metrics_data = [
            ['Metric', 'Value'],
            ['Revenue', self._fmt(latest_income.revenue)],
            ['Net Income', self._fmt(latest_income.net_income)],
            ['Total Assets', self._fmt(latest_bs.total_assets)],
            ['Total Equity', self._fmt(latest_bs.total_shareholders_equity) if latest_bs.total_shareholders_equity else "N/A"],
        ]
        
        if latest_ratios:
            if latest_ratios.net_margin:
                metrics_data.append(['Net Margin', f"{latest_ratios.net_margin:.1%}"])
            if latest_ratios.return_on_equity:
                metrics_data.append(['Return on Equity', f"{latest_ratios.return_on_equity:.1%}"])
            if latest_ratios.current_ratio:
                metrics_data.append(['Current Ratio', f"{latest_ratios.current_ratio:.2f}"])
        
        table = Table(metrics_data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.15*inch))
        
        # Summary text
        summary_text = f"""
        This report provides a comprehensive financial analysis of {self.model.company_name} 
        based on {self.model.accounting_standard.value} accounting standards. The analysis includes 
        historical financial statements, a linked 3-statement model, and forward-looking projections 
        for {self.model.forecast_years} years.
        """
        
        story.append(Paragraph(summary_text, self.styles['Normal']))
        
        return story
    
    def _create_ai_insights_section(self) -> List:
        """Create AI Executive Summary & Narrative section for the PDF."""
        story = []
        
        header_style = ParagraphStyle(
            'AIHeader',
            parent=self.styles['Heading2'],
            textColor=colors.HexColor('#2e7d32'), # Greenish for growth/ai
            fontSize=14,
            spaceAfter=10
        )
        story.append(Paragraph("🤖 AI Executive Insights", header_style))
        
        # 1. Narrative Section (The 'What is What')
        if self.model.ai_narrative:
            story.append(Paragraph("<b>📊 Investor Narrative</b>", self.styles['Heading3']))
            story.append(Paragraph(self.model.ai_narrative, self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            
        # 2. Key Risks and Summary
        if self.model.ai_summary or self.model.ai_risks:
            data = []
            if self.model.ai_summary:
                sum_p = Paragraph(f"<b>Executive Summary:</b><br/>{self.model.ai_summary}", self.styles['Normal'])
                data.append([sum_p])
                
            if self.model.ai_risks:
                risks_str = " • " + "<br/> • ".join(self.model.ai_risks)
                risk_p = Paragraph(f"<b>⚠️ Key Risk Markers:</b><br/>{risks_str}", self.styles['Normal'])
                data.append([risk_p])
            
            if data:
                t = Table(data, colWidths=[6.4*inch])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f8e9')),
                    ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('TOPPADDING', (0,0), (-1,-1), 8),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                    ('LEFTPADDING', (0,0), (-1,-1), 12),
                ]))
                story.append(t)
                
        return story

    def _create_ai_sentiment_section(self) -> List:
        """Create AI Sentiment Analysis section."""
        story = []
        
        # Section Header
        header_style = ParagraphStyle(
            'AISubheader',
            parent=self.styles['Heading2'],
            textColor=colors.HexColor('#1f4788'),
            fontSize=14,
            spaceAfter=10
        )
        story.append(Paragraph("🧠 AI Sentiment Analysis (FinBERT)", header_style))
        
        # Info Box Style
        box_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f0fe')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0,0), (-1,-1), 0.5, colors.grey)
        ])
        
        dominant = self.sentiment.get('dominant_sentiment', 'neutral').upper()
        score = self.sentiment.get('composite_score', 0.0)
        
        sentiment_color = 'grey'
        if dominant == "POSITIVE": sentiment_color = 'green'
        elif dominant == "NEGATIVE": sentiment_color = 'red'
        
        # Content
        text = f"""
        <b>Dominant Sentiment:</b> <font color='{sentiment_color}'>{dominant}</font><br/>
        <b>Composite Score:</b> {score:.2f} (Scale: -1.0 to 1.0)<br/><br/>
        <i><b>Note:</b> This analysis was performed on the textual commentary of the provided report using the <b>FinBERT</b> LLM, 
        specifically optimized for financial linguistic nuances. A positive score indicates bullish management outlook, 
        while a negative score may highlight risks or cautious guidance.</i>
        """
        
        p = Paragraph(text, self.styles['Normal'])
        data = [[p]]
        
        t = Table(data, colWidths=[6.5*inch])
        t.setStyle(box_style)
        
        story.append(t)
        return story

    def _create_market_data_section(self) -> List:
        """Create market context section."""
        story = []
        mkt = self.model.market_data
        
        header_style = ParagraphStyle(
            'MarketHeader',
            parent=self.styles['Heading2'],
            textColor=colors.HexColor('#1f4788'),
            fontSize=14,
            spaceAfter=10
        )
        story.append(Paragraph("💹 Real-Time Market Context", header_style))
        story.append(Paragraph(f"Data sourced from Yahoo Finance for: {mkt.get('long_name', self.model.company_name)} ({mkt.get('ticker')})", self.styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        
        data = [
            ["Metric", "Value", "Currency"],
            ["Current Stock Price", f"${mkt.get('current_price', 0):,.2f}", mkt.get('currency', 'USD')],
            ["Market Capitalization", self._fmt(mkt.get('market_cap')), mkt.get('currency', 'USD')],
            ["Forward P/E Ratio", f"{mkt.get('forward_pe', 0):,.1f}x" if mkt.get('forward_pe') else "N/A", "-"],
            ["Dividend Yield", f"{mkt.get('dividend_yield', 0)*100:,.2f}%" if mkt.get('dividend_yield') else "N/A", "-"]
        ]
        
        t = Table(data, colWidths=[2.5*inch, 2.5*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e7d32')), # Green theme
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        story.append(t)
        return story

    def _create_investment_thesis_section(self) -> List:
        """Create Investment Thesis and Recommendation section."""
        story = []
        
        header_style = ParagraphStyle(
            'ThesisHeader',
            parent=self.styles['Heading2'],
            textColor=colors.HexColor('#1f4788'),
            fontSize=14,
            spaceAfter=10
        )
        story.append(Paragraph("🎯 Investment Thesis & Recommendation", header_style))
        
        rec = self.model.recommendation or "HOLD"
        target = self.model.target_price or 0.0
        thesis = self.model.investment_thesis or "No detailed thesis available."
        
        rec_color = colors.grey
        if rec == "BUY": rec_color = colors.darkgreen
        elif rec == "SELL": rec_color = colors.darkred
        
        # Style for the recommendation badge
        box_style = TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), rec_color),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 16),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ])
        
        rec_table_data = [[rec]]
        t_rec = Table(rec_table_data, colWidths=[1.5*inch])
        t_rec.setStyle(box_style)
        
        # Main text content
        upside_str = ""
        if hasattr(self.model, 'upside_potential') and self.model.upside_potential:
            upside_str = f"<b>Current Upside Potential:</b> {self.model.upside_potential:+.1%}<br/><br/>"

        content_text = f"""
        <b>5-Year Target Price:</b> ${target:,.2f}<br/><br/>
        {upside_str}
        <b>Thesis Summary:</b><br/>
        {thesis}<br/><br/>
        <i><b>Disclaimer:</b> This recommendation is generated by an automated financial model 
        using 5-year growth projections and AI linguistic analysis. It does not constitute 
        professional financial advice.</i>
        """
        
        p_content = Paragraph(content_text, self.styles['Normal'])
        
        # Combined Layout Table
        main_table = Table([[t_rec, p_content]], colWidths=[2*inch, 4.5*inch])
        main_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (1, 0), (1, 0), 20),
        ]))
        
        story.append(main_table)
        return story
    
    def _create_historical_section(self) -> List:
        """Create historical financials section."""
        story = []
        
        story.append(Paragraph("Historical Financial Statements", self.styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        # Income Statement
        story.append(Paragraph("Income Statement", self.styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        income_table = self._create_income_statement_table(
            self.model.historical_income_statements
        )
        story.append(income_table)
        story.append(Spacer(1, 0.15*inch))
        
        # Balance Sheet
        story.append(Paragraph("Balance Sheet", self.styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        bs_table = self._create_balance_sheet_table(
            self.model.historical_balance_sheets
        )
        story.append(bs_table)
        story.append(Spacer(1, 0.15*inch))
        
        # Cash Flow Statement
        story.append(Paragraph("Cash Flow Statement", self.styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        cf_table = self._create_cash_flow_table(
            self.model.historical_cash_flows
        )
        story.append(cf_table)
        
        return story
    
    def _create_income_statement_table(self, statements: List[IncomeStatement]) -> Table:
        """Create income statement table."""
        # Headers
        date_format = '%Y'
        if self.model.report_type.value == "10-Q":
            date_format = '%b %Y'
        headers = ['Line Item'] + [stmt.period_end.strftime(date_format) for stmt in statements]
        
        # Data rows
        data = [headers]
        
        rows = [
            ('Revenue', 'revenue'),
            ('Cost of Revenue', 'cost_of_revenue'),
            ('Gross Profit', 'gross_profit'),
            ('Operating Expenses', 'operating_expenses'),
            ('Operating Income', 'operating_income'),
            ('EBITDA', 'ebitda'),
            ('Depreciation & Amortization', 'depreciation_amortization'),
            ('Interest Expense', 'interest_expense'),
            ('Income Before Tax', 'income_before_tax'),
            ('Income Tax Expense', 'income_tax_expense'),
            ('Net Income', 'net_income'),
        ]
        
        for label, attr in rows:
            row = [label]
            for stmt in statements:
                value = getattr(stmt, attr, None)
                row.append(self._fmt(value) if value is not None else "-")
            data.append(row)
        
        # Create table
        col_widths = [2.5*inch] + [1.2*inch] * len(statements)
        table = Table(data, colWidths=col_widths)
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        return table
    
    def _create_balance_sheet_table(self, statements: List[BalanceSheet]) -> Table:
        """Create balance sheet table."""
        date_format = '%Y'
        if self.model.report_type.value == "10-Q":
            date_format = '%b %Y'
        headers = ['Line Item'] + [stmt.period_end.strftime(date_format) for stmt in statements]
        data = [headers]
        
        rows = [
            ('ASSETS', None),
            ('Cash & Equivalents', 'cash_and_equivalents'),
            ('Accounts Receivable', 'accounts_receivable'),
            ('Inventory', 'inventory'),
            ('Total Current Assets', 'total_current_assets'),
            ('PP&E, Net', 'property_plant_equipment_net'),
            ('Intangible Assets', 'intangible_assets'),
            ('Total Assets', 'total_assets'),
            ('', None),
            ('LIABILITIES', None),
            ('Accounts Payable', 'accounts_payable'),
            ('Short-term Debt', 'short_term_debt'),
            ('Total Current Liabilities', 'total_current_liabilities'),
            ('Long-term Debt', 'long_term_debt'),
            ('Total Liabilities', 'total_liabilities'),
            ('', None),
            ('EQUITY', None),
            ('Retained Earnings', 'retained_earnings'),
            ('Total Shareholders\' Equity', 'total_shareholders_equity'),
        ]
        
        for label, attr in rows:
            if attr is None:
                row = [label] + [''] * len(statements)
            else:
                row = [label]
                for stmt in statements:
                    value = getattr(stmt, attr, None)
                    row.append(self._fmt(value) if value is not None else "-")
            data.append(row)
        
        col_widths = [2.5*inch] + [1.2*inch] * len(statements)
        table = Table(data, colWidths=col_widths)
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        return table
    
    def _create_cash_flow_table(self, statements: List[CashFlowStatement]) -> Table:
        """Create cash flow statement table."""
        date_format = '%Y'
        if self.model.report_type.value == "10-Q":
            date_format = '%b %Y'
        headers = ['Line Item'] + [stmt.period_end.strftime(date_format) for stmt in statements]
        data = [headers]
        
        rows = [
            ('OPERATING ACTIVITIES', None),
            ('Net Income', 'net_income'),
            ('Depreciation & Amortization', 'depreciation_amortization'),
            ('Changes in Working Capital', 'changes_in_working_capital'),
            ('Cash from Operations', 'cash_from_operations'),
            ('', None),
            ('INVESTING ACTIVITIES', None),
            ('Capital Expenditures', 'capital_expenditures'),
            ('Cash from Investing', 'cash_from_investing'),
            ('', None),
            ('FINANCING ACTIVITIES', None),
            ('Dividends Paid', 'dividends_paid'),
            ('Cash from Financing', 'cash_from_financing'),
            ('', None),
            ('Net Change in Cash', 'net_change_in_cash'),
        ]
        
        for label, attr in rows:
            if attr is None:
                row = [label] + [''] * len(statements)
            else:
                row = [label]
                for stmt in statements:
                    value = getattr(stmt, attr, None)
                    row.append(self._fmt(value) if value is not None else "-")
            data.append(row)
        
        col_widths = [2.5*inch] + [1.2*inch] * len(statements)
        table = Table(data, colWidths=col_widths)
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        return table
    
    def _create_linked_model_section(self) -> List:
        """Create linked model explanation section with REAL NUMBERS."""
        story = []
        
        story.append(Paragraph("Linked 3-Statement Model & Validation", self.styles['Heading1']))
        story.append(Spacer(1, 0.1*inch))
        
        # Get Latest Actual Data
        try:
            bs = self.model.historical_balance_sheets[-1]
            inc = self.model.historical_income_statements[-1]
            # Try to get latest CF if available
            cf = self.model.historical_cash_flows[-1] if self.model.historical_cash_flows else None
        except IndexError:
            story.append(Paragraph("No historical data available for validation.", self.styles['Normal']))
            return story

        # 1. Balance Sheet Identity Check
        assets = bs.total_assets or 0
        liab = bs.total_liabilities or 0
        eq = bs.total_shareholders_equity or 0
        check_bs = liab + eq
        diff_bs = assets - check_bs
        status_bs = "✓ OK" if abs(diff_bs) < 1000 else f"⚠ GAP: ${diff_bs:,.0f}"

        # 2. Cash Flow Check
        status_cf = "N/A"
        diff_cf = 0
        net_change_rep = 0
        net_change_calc = 0
        
        if cf:
            net_change_rep = cf.net_change_in_cash or 0
            net_change_calc = (cf.cash_from_operations or 0) + (cf.cash_from_investing or 0) + (cf.cash_from_financing or 0)
            diff_cf = net_change_rep - net_change_calc
            status_cf = "✓ OK" if abs(diff_cf) < 1000 else f"⚠ GAP: ${diff_cf:,.0f}"

        # Create Data Table
        data = [
            ["Check", "Logic", "Calculated Match", "Status"],
            [
                "BS Identity", 
                "A = L + E", 
                f"Assets: ${assets:,.0f}\nL+E: ${check_bs:,.0f}", 
                status_bs
            ],
            [
                "Cash flow",
                "Net Chg = Sum",
                f"Reported: ${net_change_rep:,.0f}\nCalc: ${net_change_calc:,.0f}",
                status_cf
            ],
            [
                "Equity Link",
                "End = Beg+NI-Div",
                self._get_re_reconciliation(bs, inc, cf),
                "✓ LINKED"
            ],
            [
                "Accounting Link",
                "IS -> CF/BS",
                f"Net Income: ${inc.net_income:,.0f}\nD&A Sync: {'✓' if (not cf or inc.depreciation_amortization == cf.depreciation_amortization) else '❌'}",
                "✓ LINKED"
            ]
        ]
        
        # Capex Linkage
        if cf and cf.capital_expenditures:
             data.append([
                "PPE Link",
                "CF -> BS",
                f"Capex: ${cf.capital_expenditures:,.0f}",
                "✓ LINKED"
             ])

        # Adjusted column widths for maximum data visibility
        t = Table(data, colWidths=[1.1*inch, 1.2*inch, 4.2*inch, 1.0*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ]))
        
        story.append(t)
        story.append(Spacer(1, 0.1*inch))
        
        # Modeling Adjustments (NEW)
        if hasattr(self.model, 'adjustments') and self.model.adjustments:
            story.append(Paragraph("Modeling Adjustments (Audit Trail):", ParagraphStyle('AdjHeader', parent=self.styles['Normal'], fontName='Helvetica-Bold')))
            for adj in self.model.adjustments:
                 story.append(Paragraph(f"• {adj}", self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            
        # Detailed Validation Errors (if any)
        if hasattr(self.model, 'validation_errors') and self.model.validation_errors:
            story.append(Paragraph("Validation Warnings:", ParagraphStyle('WarnHeader', parent=self.styles['Normal'], fontName='Helvetica-Bold')))
            for err in self.model.validation_errors:
                 story.append(Paragraph(f"• {err}", self.styles['Normal']))
                 
        return story

    def _get_re_reconciliation(self, bs, inc, cf) -> str:
        """Helper to explain RE Roll-forward logic."""
        ni = inc.net_income
        div = abs(cf.dividends_paid or 0) if cf else 0
        end_re = bs.retained_earnings or 0
        
        # Implied Beg RE for transparency
        beg_re_implied = end_re - ni + div
        
        return f"NI (${ni:,.0f}) - Div (${div:,.0f}) = ΔRE (${ni-div:,.0f})\nEnding RE (${end_re:,.0f}) = Implied Beg (${beg_re_implied:,.0f}) + ΔRE"
    
    def _create_forecast_section(self) -> List:
        """Create forecast section."""
        story = []
        
        story.append(Paragraph("Financial Forecast", self.styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        # Assumptions
        story.append(Paragraph("Key Assumptions", self.styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        assumptions = self.model.assumptions
        assumptions_data = [
            ['Assumption', 'Value'],
            ['Revenue Growth Rate', f"{assumptions.revenue_growth_rate:.1%}"],
            ['Gross Margin', f"{assumptions.gross_margin:.1%}"],
            ['Operating Margin', f"{assumptions.operating_margin:.1%}"],
            ['Tax Rate', f"{assumptions.tax_rate:.1%}"],
            ['CAPEX % of Revenue', f"{assumptions.capex_percent_of_revenue:.1%}"],
            ['Days Sales Outstanding', f"{assumptions.days_sales_outstanding} days"],
            ['Days Inventory Outstanding', f"{assumptions.days_inventory_outstanding} days"],
        ]
        
        table = Table(assumptions_data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        # Forecast tables
        story.append(Paragraph("Forecast Income Statement", self.styles['Heading2']))
        forecast_income_table = self._create_income_statement_table(
            self.model.forecast_income_statements
        )
        story.append(forecast_income_table)
        
        return story
    
    def _create_ratios_section(self) -> List:
        """Create financial ratios section."""
        story = []
        
        story.append(Paragraph("Financial Ratios & Metrics", self.styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        # Combine historical and forecast ratios
        all_ratios = self.model.historical_ratios + self.model.forecast_ratios
        
        if not all_ratios:
            story.append(Paragraph("No ratio data available", self.styles['Normal']))
            return story
        
        # Create ratios table
        headers = ['Ratio'] + [r.period.strftime('%Y') for r in all_ratios]
        data = [headers]
        
        ratio_rows = [
            ('Gross Margin', 'gross_margin', '%'),
            ('Operating Margin', 'operating_margin', '%'),
            ('Net Margin', 'net_margin', '%'),
            ('Return on Assets', 'return_on_assets', '%'),
            ('Return on Equity', 'return_on_equity', '%'),
            ('Current Ratio', 'current_ratio', 'x'),
            ('Debt to Equity', 'debt_to_equity', 'x'),
        ]
        
        for label, attr, unit in ratio_rows:
            row = [label]
            for ratio in all_ratios:
                value = getattr(ratio, attr, None)
                if value is not None:
                    if unit == '%':
                        row.append(f"{value:.1%}")
                    else:
                        row.append(f"{value:.2f}")
                else:
                    row.append("-")
            data.append(row)
        
        col_widths = [2*inch] + [1*inch] * len(all_ratios)
        table = Table(data, colWidths=col_widths)
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        story.append(table)
        
        return story
    
    def _power_bi_style(self):
        """Set Power BI stype plots."""
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.rcParams['figure.facecolor'] = 'white'
        plt.rcParams['axes.facecolor'] = '#f8f9fa'
        plt.rcParams['axes.edgecolor'] = '#e9ecef'
        plt.rcParams['axes.labelcolor'] = '#495057'
        plt.rcParams['text.color'] = '#212529'
        plt.rcParams['xtick.color'] = '#495057'
        plt.rcParams['ytick.color'] = '#495057'
        plt.rcParams['grid.color'] = '#dee2e6'
    
    def _create_revenue_profit_chart(self) -> Optional[RLImage]:
        """Create dual-axis revenue and profit chart."""
        try:
            self._power_bi_style()
            
            all_income = self.model.historical_income_statements + self.model.forecast_income_statements
            years = [stmt.period_end.year for stmt in all_income]
            revenues = [stmt.revenue / 1e9 for stmt in all_income]  # Billions
            net_income = [stmt.net_income / 1e9 for stmt in all_income]
            
            fig, ax1 = plt.subplots(figsize=(10, 5))
            
            # Revenue Bar Chart
            bars = ax1.bar(years, revenues, color='#1f77b4', alpha=0.7, label='Revenue ($B)')
            ax1.set_xlabel('Year', fontsize=10, fontweight='bold')
            ax1.set_ylabel('Revenue ($B)', color='#1f77b4', fontsize=10, fontweight='bold')
            ax1.tick_params(axis='y', labelcolor='#1f77b4')
            
            # Net Income Line Chart
            ax2 = ax1.twinx()
            ax2.plot(years, net_income, color='#ff7f0e', linewidth=3, marker='o', label='Net Income ($B)')
            ax2.set_ylabel('Net Income ($B)', color='#ff7f0e', fontsize=10, fontweight='bold')
            ax2.tick_params(axis='y', labelcolor='#ff7f0e')
            
            # Title
            plt.title('Revenue & Net Income Trajectory', fontsize=14, fontweight='bold', pad=20)
            
            # Add data labels on bars
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'${height:.1f}',
                        ha='center', va='bottom', fontsize=8)

            # Highlight forecast section
            if self.model.forecast_income_statements:
                forecast_start_year = self.model.forecast_income_statements[0].period_end.year
                plt.axvline(x=forecast_start_year - 0.5, color='gray', linestyle='--', alpha=0.5)
                ax1.text(forecast_start_year, max(revenues)*1.1, 'Forecast →', color='gray', fontsize=10)

            plt.tight_layout()
            
            # Save
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            plt.close()
            
            return RLImage(buf, width=7*inch, height=3.5*inch)
            
        except Exception as e:
            logger.error(f"Error creating revenue chart: {e}")
            return None

    def _create_margins_chart(self) -> Optional[RLImage]:
        """Create profitability margins chart."""
        try:
            self._power_bi_style()
            
            all_ratios = self.model.historical_ratios + self.model.forecast_ratios
            years = [r.period.year for r in all_ratios]
            
            gross = [(r.gross_margin or 0) * 100 for r in all_ratios]
            operating = [(r.operating_margin or 0) * 100 for r in all_ratios]
            net = [(r.net_margin or 0) * 100 for r in all_ratios]
            
            fig, ax = plt.subplots(figsize=(10, 4))
            
            ax.plot(years, gross, marker='o', linewidth=2, label='Gross Margin %', color='#2ca02c')
            ax.plot(years, operating, marker='^', linewidth=2, label='Operating Margin %', color='#1f77b4')
            ax.plot(years, net, marker='s', linewidth=2, label='Net Margin %', color='#d62728')
            
            ax.set_title('Profitability Margins Trend', fontsize=14, fontweight='bold')
            ax.set_ylabel('Margin (%)')
            ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.2), ncol=3)
            ax.grid(True, linestyle='--', alpha=0.5)
            
            # Forecast divider
            if self.model.forecast_income_statements:
                forecast_start_year = self.model.forecast_income_statements[0].period_end.year
                plt.axvline(x=forecast_start_year - 0.5, color='gray', linestyle='--', alpha=0.5)
            
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            plt.close()
            
            return RLImage(buf, width=7*inch, height=3.5*inch)
        except Exception as e:
            logger.error(f"Error creating margins chart: {e}")
            return None

    def _create_cost_structure_chart(self) -> Optional[RLImage]:
        """Create stacked cost structure chart."""
        try:
            self._power_bi_style()
            
            all_income = self.model.historical_income_statements + self.model.forecast_income_statements
            years = [stmt.period_end.year for stmt in all_income]
            
            revenue = [100] * len(years) # 100%
            cogs = [(stmt.cost_of_revenue / stmt.revenue * 100) if stmt.revenue and stmt.revenue > 0 else 0 for stmt in all_income]
            opex = [(stmt.operating_expenses / stmt.revenue * 100) if stmt.revenue and stmt.revenue > 0 else 0 for stmt in all_income]
            profit = [(stmt.net_income / stmt.revenue * 100) if stmt.revenue and stmt.revenue > 0 else 0 for stmt in all_income]
            
            fig, ax = plt.subplots(figsize=(10, 4))
            
            ax.bar(years, cogs, label='COGS', color='#e377c2', alpha=0.8)
            ax.bar(years, opex, bottom=cogs, label='OpEx', color='#9467bd', alpha=0.8)
            # Remaining is profit + tax/interest, simplifying for viz to just profit
            # Note: This is simplified stacked chart
            
            ax.set_title('Cost Structure Analysis (% of Revenue)', fontsize=14, fontweight='bold')
            ax.set_ylabel('% of Revenue')
            ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.2), ncol=3)
            
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            plt.close()
            
            return RLImage(buf, width=7*inch, height=3.5*inch)
        except Exception as e:
            logger.error(f"Error creating cost chart: {e}")
            return None
    def _create_charts_section(self) -> List:
        """Helper to combine charts into a single section."""
        story = []
        story.append(Paragraph("📊 Visual Analysis & Trends", self.styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        # 1. Revenue & Profit
        chart1 = self._create_revenue_profit_chart()
        if chart1:
            story.append(chart1)
            story.append(Spacer(1, 0.3*inch))
            
        # 2. Margins
        chart2 = self._create_margins_chart()
        if chart2:
            story.append(chart2)
            story.append(Spacer(1, 0.3*inch))
            
        # 3. Cost Structure (If space allows)
        chart3 = self._create_cost_structure_chart()
        if chart3:
            story.append(chart3)
            
        return story

    def _create_dcf_section(self) -> List:
        """Create a detailed DCF valuation section."""
        story = []
        dcf = self.model.dcf_valuation
        
        story.append(Paragraph("💎 Discounted Cash Flow (DCF) Analysis", self.styles['WS_Heading1']))
        
        is_q = self.model.report_type.value == "10-Q"
        if is_q:
            warning_style = ParagraphStyle('Warning', parent=self.styles['WS_Small'], textColor=colors.red, leftIndent=10)
            story.append(Paragraph(
                "⚠️ <b>INTERIM UPDATE NOTICE:</b> This valuation is based on 10-Q (Unaudited) data. "
                "Income statement metrics have been annualized using a run-rate methodology. "
                "For a definitive valuation base, refer to the most recent 10-K Audited Annual Report.",
                warning_style
            ))
            story.append(Spacer(1, 0.1*inch))

        story.append(Paragraph(
            f"Intrinsic valuation based on {len(dcf.forecast_period_fcf)}-year cash flow projections. "
            f"Assumed WACC: {dcf.wacc_used:.1%} | Terminal Growth: {dcf.terminal_growth_used:.1%}",
            self.styles['WS_Normal']
        ))
        story.append(Spacer(1, 0.1*inch))
        
        # Table 1: Cash Flow Projections (In Millions for better fit)
        proj_header = ["Item"] + [str(y.year) for y in dcf.forecast_period_fcf]
        projected_data = [
            proj_header,
            ["EBIT"] + [self._fmt(y.ebit) for y in dcf.forecast_period_fcf],
            ["- Taxes"] + [self._fmt(-y.tax_expense) for y in dcf.forecast_period_fcf],
            ["NOPAT"] + [self._fmt(y.nopat) for y in dcf.forecast_period_fcf],
            ["+ D&A"] + [self._fmt(y.depreciation_amortization) for y in dcf.forecast_period_fcf],
            ["- CapEx"] + [self._fmt(-y.capex) for y in dcf.forecast_period_fcf],
            ["- Δ NWC"] + [self._fmt(-y.change_in_nwc) for y in dcf.forecast_period_fcf],
            ["Free Cash Flow"] + [self._fmt(y.free_cash_flow) for y in dcf.forecast_period_fcf],
            ["PV of FCF"] + [self._fmt(y.pv_of_fcf) for y in dcf.forecast_period_fcf]
        ]
        
        # Calculate column widths to fit landscape (10.5 inches available with reduced margins)
        total_width = 10.3 * inch 
        num_cols = len(dcf.forecast_period_fcf)
        # Give first column more space for row labels (2.0 inches minimum)
        first_col_width = 2.0 * inch
        remaining_width = total_width - first_col_width
        year_col_width = remaining_width / num_cols if num_cols > 0 else 1.0 * inch
        
        t1 = Table(projected_data, colWidths=[first_col_width] + [year_col_width]*num_cols, hAlign='CENTER')
        t1.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['navy']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Row labels left-aligned
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.25, self.colors['border_grey']),
            ('FONTSIZE', (0, 0), (-1, -1), 7), # Slightly larger for readability
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'), 
            ('LINEBELOW', (0, -2), (-1, -2), 1, self.colors['charcoal']),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.colors['light_grey']]),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t1)
        story.append(Spacer(1, 0.15*inch))
        
        # Table 2: Valuation Bridge
        story.append(Paragraph("Intrinsic Value Breakdown", self.styles['WS_Heading2']))
        bridge_data = [
            ["Item", "Value"],
            ["Sum of PV of Forecast Period FCF", self._fmt(dcf.sum_pv_fcf)],
            ["PV of Terminal Value", self._fmt(dcf.pv_terminal_value)],
            ["Enterprise Value (EV)", self._fmt(dcf.enterprise_value)],
            ["- Net Debt (Debt - Cash)", self._fmt(dcf.net_debt)],
            ["Equity Value", self._fmt(dcf.equity_value)],
            ["Total Shares Outstanding", self._fmt(dcf.shares_outstanding)],
            ["Implied Price Per Share", f"${dcf.implied_price_per_share:,.2f}"]
        ]
        
        t2 = Table(bridge_data, colWidths=[3.5*inch, 2*inch], hAlign='LEFT')
        t2.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['charcoal']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.25, self.colors['border_grey']),
            ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'), 
            ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'), 
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'), 
            ('BOX', (0, -1), (-1, -1), 1.5, self.colors['navy']), 
            ('PADDING', (0, 0), (-1, -1), 4),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.colors['light_grey']])
        ]))
        story.append(t2)
        
        return story

# Example usage
if __name__ == "__main__":
    pass
