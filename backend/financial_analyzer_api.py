"""
Financial Analyzer API endpoints
Integrates finanalyzer functionality into the FinvizPro application
"""

from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename
import os
import traceback
from pathlib import Path
from datetime import date
import json
import io
import base64

# Import finanalyzer modules
try:
    from finanalyzer.core.pdf_parser import PDFParser
    from finanalyzer.core.gaap_ifrs_classifier import GaapIfrsClassifier
    from finanalyzer.core.financial_extractor import FinancialExtractor
    from finanalyzer.core.model_engine import ModelEngine
    from finanalyzer.core.forecast_engine import ForecastEngine
    from finanalyzer.core.report_generator import ReportGenerator
    from finanalyzer.models.schemas import (
        FinancialStatements,
        IncomeStatement,
        BalanceSheet,
        CashFlowStatement,
        AccountingStandard,
        ReportType,
        Currency,
        ForecastAssumptions
    )
    from finanalyzer.core.markov_integration import run_markov_chain_analysis
    FINANALYZER_AVAILABLE = True
except ImportError:
    FINANALYZER_AVAILABLE = False
    print("Warning: finanalyzer modules not available")

# Create Blueprint
analyzer_bp = Blueprint('analyzer', __name__, url_prefix='/api/analyzer')

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'pdf'}

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@analyzer_bp.route('/status')
def status():
    """Check if financial analyzer is available"""
    return jsonify({
        'available': FINANALYZER_AVAILABLE,
        'features': {
            'pdf_parsing': FINANALYZER_AVAILABLE,
            'gaap_ifrs_classification': FINANALYZER_AVAILABLE,
            'financial_extraction': FINANALYZER_AVAILABLE,
            'model_building': FINANALYZER_AVAILABLE,
            'forecasting': FINANALYZER_AVAILABLE,
            'report_generation': FINANALYZER_AVAILABLE
        }
    })


@analyzer_bp.route('/upload', methods=['POST'])
def upload_pdf():
    """Upload a financial report PDF for analysis"""
    if not FINANALYZER_AVAILABLE:
        return jsonify({'error': 'Financial analyzer not available'}), 503
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'message': 'File uploaded successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@analyzer_bp.route('/parse', methods=['POST'])
def parse_pdf():
    """Parse a PDF and extract basic information"""
    if not FINANALYZER_AVAILABLE:
        return jsonify({'error': 'Financial analyzer not available'}), 503
    
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Parse PDF
        parser = PDFParser(filepath)
        extracted_data = parser.extract()
        
        return jsonify({
            'success': True,
            'total_pages': extracted_data['total_pages'],
            'tables_found': len(extracted_data['tables']),
            'text_length': len(extracted_data['text']),
            'metadata': extracted_data.get('metadata', {})
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@analyzer_bp.route('/classify', methods=['POST'])
def classify_standard():
    """Classify accounting standard (GAAP vs IFRS)"""
    if not FINANALYZER_AVAILABLE:
        return jsonify({'error': 'Financial analyzer not available'}), 503
    
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Parse PDF
        parser = PDFParser(filepath)
        extracted_data = parser.extract()
        
        # Classify
        classifier = GaapIfrsClassifier()
        standard, confidence, evidence = classifier.classify(
            extracted_data['text'],
            extracted_data['tables']
        )
        
        return jsonify({
            'success': True,
            'standard': standard.value,
            'confidence': float(confidence),
            'evidence': evidence
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@analyzer_bp.route('/extract', methods=['POST'])
def extract_financials():
    """Extract financial statements from PDF"""
    if not FINANALYZER_AVAILABLE:
        return jsonify({'error': 'Financial analyzer not available'}), 503
    
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Parse PDF
        parser = PDFParser(filepath)
        extracted_data = parser.extract()
        
        # Extract financial statements
        pages_dict = {i+1: text for i, text in enumerate(extracted_data['pages'])}
        extractor = FinancialExtractor(pages_dict)
        statements = extractor.extract()
        
        # Convert to JSON-serializable format
        result = {
            'success': True,
            'company_name': statements.company_name,
            'ticker': statements.ticker,
            'fiscal_year': statements.fiscal_year,
            'currency': statements.currency.value,
            'accounting_standard': statements.accounting_standard.value,
            'income_statements': [],
            'balance_sheets': [],
            'cash_flow_statements': []
        }
        
        # Add income statements
        for inc in statements.income_statements:
            result['income_statements'].append({
                'period_start': inc.period_start.isoformat() if inc.period_start else None,
                'period_end': inc.period_end.isoformat() if inc.period_end else None,
                'revenue': float(inc.revenue) if inc.revenue else 0,
                'gross_profit': float(inc.gross_profit) if inc.gross_profit else 0,
                'operating_income': float(inc.operating_income) if inc.operating_income else 0,
                'net_income': float(inc.net_income) if inc.net_income else 0,
                'ebitda': float(inc.ebitda) if inc.ebitda else 0,
                'diluted_eps': float(inc.diluted_eps) if inc.diluted_eps else 0
            })
        
        # Add balance sheets
        for bs in statements.balance_sheets:
            result['balance_sheets'].append({
                'period_end': bs.period_end.isoformat() if bs.period_end else None,
                'total_assets': float(bs.total_assets) if bs.total_assets else 0,
                'total_liabilities': float(bs.total_liabilities) if bs.total_liabilities else 0,
                'total_shareholders_equity': float(bs.total_shareholders_equity) if bs.total_shareholders_equity else 0,
                'cash_and_equivalents': float(bs.cash_and_equivalents) if bs.cash_and_equivalents else 0
            })
        
        # Add cash flow statements
        for cf in statements.cash_flow_statements:
            result['cash_flow_statements'].append({
                'period_start': cf.period_start.isoformat() if cf.period_start else None,
                'period_end': cf.period_end.isoformat() if cf.period_end else None,
                'cash_from_operations': float(cf.cash_from_operations) if cf.cash_from_operations else 0,
                'cash_from_investing': float(cf.cash_from_investing) if cf.cash_from_investing else 0,
                'cash_from_financing': float(cf.cash_from_financing) if cf.cash_from_financing else 0,
                'net_change_in_cash': float(cf.net_change_in_cash) if cf.net_change_in_cash else 0
            })
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@analyzer_bp.route('/model', methods=['POST'])
def build_model():
    """Build linked 3-statement model"""
    if not FINANALYZER_AVAILABLE:
        return jsonify({'error': 'Financial analyzer not available'}), 503
    
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Parse and extract
        parser = PDFParser(filepath)
        extracted_data = parser.extract()
        
        pages_dict = {i+1: text for i, text in enumerate(extracted_data['pages'])}
        extractor = FinancialExtractor(pages_dict)
        statements = extractor.extract()
        
        # Build model
        model_engine = ModelEngine(statements)
        linked_model = model_engine.build_linked_model()
        
        # Get summary metrics
        summary = model_engine.get_summary_metrics()
        
        return jsonify({
            'success': True,
            'is_balanced': linked_model.is_balanced,
            'validation_errors': linked_model.validation_errors[:10],  # First 10 errors
            'summary': summary
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@analyzer_bp.route('/forecast', methods=['POST'])
def generate_forecast():
    """Generate financial forecast"""
    if not FINANALYZER_AVAILABLE:
        return jsonify({'error': 'Financial analyzer not available'}), 503
    
    try:
        data = request.json
        filename = data.get('filename')
        years = data.get('years', 5)
        scenario = data.get('scenario', 'base')
        
        # Get assumptions from request or use defaults
        assumptions_data = data.get('assumptions', {})
        
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Parse, extract, and build model
        parser = PDFParser(filepath)
        extracted_data = parser.extract()
        
        pages_dict = {i+1: text for i, text in enumerate(extracted_data['pages'])}
        extractor = FinancialExtractor(pages_dict)
        statements = extractor.extract()
        
        model_engine = ModelEngine(statements)
        linked_model = model_engine.build_linked_model()
        
        # Create forecast assumptions
        forecast_assumptions = ForecastAssumptions(
            revenue_growth_rate=assumptions_data.get('revenue_growth_rate', 0.08),
            gross_margin=assumptions_data.get('gross_margin', 0.42),
            operating_margin=assumptions_data.get('operating_margin', 0.22),
            tax_rate=assumptions_data.get('tax_rate', 0.21),
            capex_percent_of_revenue=assumptions_data.get('capex_percent_of_revenue', 0.06),
            days_sales_outstanding=assumptions_data.get('days_sales_outstanding', 45),
            days_inventory_outstanding=assumptions_data.get('days_inventory_outstanding', 60),
            days_payable_outstanding=assumptions_data.get('days_payable_outstanding', 35)
        )
        
        # Generate forecast
        forecast_engine = ForecastEngine(linked_model)
        forecast_model = forecast_engine.forecast(
            years=years,
            assumptions=forecast_assumptions,
            scenario=scenario
        )
        
        # Prepare forecast data for response
        forecast_data = {
            'success': True,
            'forecast_years': forecast_model.forecast_years,
            'scenario': scenario,
            'assumptions': {
                'revenue_growth_rate': forecast_assumptions.revenue_growth_rate,
                'gross_margin': forecast_assumptions.gross_margin,
                'operating_margin': forecast_assumptions.operating_margin,
                'tax_rate': forecast_assumptions.tax_rate
            },
            'projections': []
        }
        
        # Add projected statements
        for i, inc in enumerate(forecast_model.forecasted_income_statements):
            projection = {
                'year': i + 1,
                'revenue': float(inc.revenue) if inc.revenue else 0,
                'gross_profit': float(inc.gross_profit) if inc.gross_profit else 0,
                'operating_income': float(inc.operating_income) if inc.operating_income else 0,
                'net_income': float(inc.net_income) if inc.net_income else 0,
                'ebitda': float(inc.ebitda) if inc.ebitda else 0
            }
            forecast_data['projections'].append(projection)
        
        return jsonify(forecast_data)
    
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@analyzer_bp.route('/report', methods=['POST'])
def generate_report():
    """Generate comprehensive PDF report"""
    if not FINANALYZER_AVAILABLE:
        return jsonify({'error': 'Financial analyzer not available'}), 503
    
    try:
        data = request.json
        filename = data.get('filename')
        years = data.get('years', 5)
        
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Full pipeline
        parser = PDFParser(filepath)
        extracted_data = parser.extract()
        
        pages_dict = {i+1: text for i, text in enumerate(extracted_data['pages'])}
        extractor = FinancialExtractor(pages_dict)
        statements = extractor.extract()
        
        model_engine = ModelEngine(statements)
        linked_model = model_engine.build_linked_model()
        
        forecast_engine = ForecastEngine(linked_model)
        forecast_model = forecast_engine.forecast(years=years, scenario='base')
        
        # Generate report
        report_filename = f"analysis_{statements.company_name.replace(' ', '_')}.pdf"
        report_path = os.path.join(OUTPUT_FOLDER, report_filename)
        
        generator = ReportGenerator(forecast_model)
        generator.generate_pdf(report_path)
        
        return jsonify({
            'success': True,
            'report_filename': report_filename,
            'download_url': f'/api/analyzer/download/{report_filename}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@analyzer_bp.route('/download/<filename>')
def download_report(filename):
    """Download generated report"""
    try:
        filepath = os.path.join(OUTPUT_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analyzer_bp.route('/demo/sample-data')
def get_sample_data():
    """Get sample financial data for demonstration"""
    return jsonify({
        'company_name': 'TechCorp Inc.',
        'ticker': 'TECH',
        'fiscal_year': 2023,
        'currency': 'USD',
        'accounting_standard': 'GAAP',
        'income_statement': {
            'revenue': 1000000000,
            'gross_profit': 400000000,
            'operating_income': 200000000,
            'net_income': 150000000,
            'ebitda': 250000000,
            'diluted_eps': 1.50
        },
        'balance_sheet': {
            'total_assets': 1200000000,
            'total_liabilities': 450000000,
            'total_shareholders_equity': 750000000,
            'cash_and_equivalents': 150000000
        },
        'cash_flow': {
            'cash_from_operations': 180000000,
            'cash_from_investing': -60000000,
            'cash_from_financing': -30000000,
            'net_change_in_cash': 20000000
        }
    })


@analyzer_bp.route('/markov', methods=['POST'])
def analyze_markov():
    """Run Markov Chain analysis on a stock"""
    if not FINANALYZER_AVAILABLE:
        return jsonify({'error': 'Financial analyzer not available'}), 503
    
    try:
        data = request.json
        ticker = data.get('ticker')
        period = data.get('period', '2y')
        n_states = int(data.get('n_states', 5))
        method = data.get('method', 'returns')
        n_days = int(data.get('n_days', 5))
        
        if not ticker:
            return jsonify({'error': 'Ticker is required'}), 400
        
        # Run analysis (captures output and generates plots if needed)
        console_output, predictions, hist_data, viz, discretizer, model = run_markov_chain_analysis(
            ticker, period, n_states, method, n_days
        )
        
        if predictions is None:
             return jsonify({
                'success': False,
                'log': console_output,
                'error': 'Analysis failed. Check logs.'
            }), 500

        # Prepare response data
        response = {
            'success': True,
            'ticker': ticker,
            'current_price': hist_data['Close'].iloc[-1],
            'last_date': hist_data.index[-1].strftime('%Y-%m-%d'),
            'predictions': [],
            'transition_matrix': [], 
            'states_description': discretizer.describe_states(),
            'log': console_output,
            'summary': None # Placeholder for structured analysis
        }

        # Calculate structured summary if possible (Mainly for 1-day forecast)
        if 'probability_up' in predictions:
            # Extract metrics
            prob_up = predictions['probability_up']
            prob_down = predictions['probability_down']
            exp_return = predictions['expected_return']
            ret_std = predictions.get('return_std', 0)
            
            # 1. Recommendation Logic
            signal = "HOLD"
            confidence = "Medium"
            if prob_up > 0.65 and exp_return > 0.01:
                signal = "STRONG BUY"
                confidence = "High"
            elif prob_up > 0.55 and exp_return > 0.005:
                signal = "BUY"
                confidence = "Medium"
            elif prob_up < 0.35 and exp_return < -0.01:
                signal = "STRONG SELL"
                confidence = "High"
            elif prob_up < 0.45 and exp_return < -0.005:
                signal = "SELL"
                confidence = "Medium"

            # 2. Risk Logic (VaR calculation)
            # Need simulated returns for strict VaR, but can approximate or use if available
            risk_data = {}
            if 'simulated_returns' in predictions:
                import numpy as np
                sim_returns = np.array(predictions['simulated_returns'])
                current_price = predictions['current_price']
                
                # VaR 95%
                var_percentile = 5
                var_return = np.percentile(sim_returns, var_percentile)
                var_loss = current_price * abs(var_return) if var_return < 0 else 0
                
                # CVaR (Expected Shortfall)
                cvar_returns = sim_returns[sim_returns <= var_return]
                cvar_return = np.mean(cvar_returns) if len(cvar_returns) > 0 else var_return
                cvar_loss = current_price * abs(cvar_return) if cvar_return < 0 else 0
                
                risk_data = {
                    'var_95_loss': var_loss,
                    'var_95_pct': var_return * 100,
                    'cvar_loss': cvar_loss,
                    'cvar_pct': cvar_return * 100,
                    'volatility': ret_std * 100
                }

            response['summary'] = {
                'recommendation': {
                    'signal': signal,
                    'confidence': confidence,
                    'prob_up': prob_up * 100,
                    'prob_down': prob_down * 100
                },
                'risk': risk_data
            }

        # Format predictions
        current_price = hist_data['Close'].iloc[-1]
        if 'daily_predictions' in predictions:
            for pred in predictions['daily_predictions']:
                # Calculate percent change if missing
                expected_price = pred['expected_price']
                if 'expected_change_pct' in pred:
                    pct_change = float(pred['expected_change_pct'])
                else:
                    pct_change = ((expected_price - current_price) / current_price) * 100
                    
                response['predictions'].append({
                    'day': pred['day'],
                    'expected_price': expected_price,
                    'expected_change_pct': pct_change,
                    'lower_bound': pred.get('confidence_95_lower', pred.get('lower_bound_95', 0)),
                    'upper_bound': pred.get('confidence_95_upper', pred.get('upper_bound_95', 0))
                })
        else:
            # Handle single day prediction (structure is different)
            expected_price = predictions.get('expected_price', 0)
            if 'expected_return' in predictions:
                pct_change = predictions['expected_return'] * 100
            else:
                pct_change = ((expected_price - current_price) / current_price) * 100

            response['predictions'].append({
                'day': 1,
                'expected_price': expected_price,
                'expected_change_pct': pct_change,
                'lower_bound': predictions.get('confidence_95_lower', 0),
                'upper_bound': predictions.get('confidence_95_upper', 0)
            })
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500
