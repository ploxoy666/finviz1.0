"""
GAAP vs IFRS Classifier
Automatically detects accounting standard used in financial statements.
"""

import re
from typing import Dict, List, Tuple
from enum import Enum

from loguru import logger

from ..models.schemas import AccountingStandard


class GaapIfrsClassifier:
    """
    Classifier to detect whether financial statements follow GAAP or IFRS.
    Uses multiple detection methods for robust classification.
    """
    
    # GAAP-specific indicators
    GAAP_INDICATORS = {
        'keywords': [
            'generally accepted accounting principles',
            'us gaap',
            'fasb',
            'asc 606',
            'asc 842',
            'sfas',
            'lifo',
            'last-in, first-out',
            'extraordinary items',
            'sec',
            'form 10-k',
            'form 10-q'
        ],
        'statement_names': [
            'statement of operations',
            'statement of stockholders\' equity'
        ],
        'line_items': [
            'treasury stock',
            'additional paid-in capital',
            'research and development expense'  # Always expensed in GAAP
        ],
        'policies': [
            'lifo method',
            'development costs are expensed',
            'no revaluation of property',
            'extraordinary items'
        ]
    }
    
    # IFRS-specific indicators
    IFRS_INDICATORS = {
        'keywords': [
            'international financial reporting standards',
            'ifrs',
            'ias',
            'iasb',
            'ifrs 15',
            'ifrs 16',
            'ifrs 9',
            'revaluation reserve',
            'other comprehensive income',
            'fifo',
            'weighted average'
        ],
        'statement_names': [
            'statement of comprehensive income',
            'statement of financial position',
            'statement of changes in equity'
        ],
        'line_items': [
            'revaluation surplus',
            'other comprehensive income',
            'development costs capitalized',
            'finance costs'
        ],
        'policies': [
            'revaluation model',
            'development costs capitalized',
            'impairment reversal',
            'functional currency'
        ]
    }
    
    def __init__(self):
        """Initialize classifier."""
        self.detection_scores = {
            'gaap': 0.0,
            'ifrs': 0.0
        }
        self.evidence = {
            'gaap': [],
            'ifrs': []
        }
    
    def classify(self, text: str, tables: List[Dict] = None) -> Tuple[AccountingStandard, float, Dict]:
        """
        Classify accounting standard.
        
        Args:
            text: Full text of financial report
            tables: Extracted tables (optional)
            
        Returns:
            Tuple of (standard, confidence, evidence_dict)
        """
        logger.info("Starting GAAP/IFRS classification...")
        
        # Reset scores
        self.detection_scores = {'gaap': 0.0, 'ifrs': 0.0}
        self.evidence = {'gaap': [], 'ifrs': []}
        
        text_lower = text.lower()
        
        # Method 1: Keyword detection
        self._detect_keywords(text_lower)
        
        # Method 2: Statement name detection
        self._detect_statement_names(text_lower)
        
        # Method 3: Line item detection
        self._detect_line_items(text_lower)
        
        # Method 4: Accounting policy detection
        self._detect_policies(text_lower)
        
        # Method 5: Regulatory references
        self._detect_regulatory_refs(text_lower)
        
        # Calculate final scores
        gaap_score = self.detection_scores['gaap']
        ifrs_score = self.detection_scores['ifrs']
        
        # Determine standard
        if gaap_score > ifrs_score and gaap_score > 3:
            standard = AccountingStandard.GAAP
            confidence = min(gaap_score / (gaap_score + ifrs_score + 0.01), 0.99)
        elif ifrs_score > gaap_score and ifrs_score > 3:
            standard = AccountingStandard.IFRS
            confidence = min(ifrs_score / (gaap_score + ifrs_score + 0.01), 0.99)
        else:
            standard = AccountingStandard.UNKNOWN
            confidence = 0.0
        
        evidence_summary = {
            'gaap_score': gaap_score,
            'ifrs_score': ifrs_score,
            'gaap_evidence': self.evidence['gaap'],
            'ifrs_evidence': self.evidence['ifrs'],
            'total_evidence': len(self.evidence['gaap']) + len(self.evidence['ifrs'])
        }
        
        logger.info(f"Classification: {standard.value} (confidence: {confidence:.2%})")
        logger.debug(f"Scores - GAAP: {gaap_score}, IFRS: {ifrs_score}")
        
        return standard, confidence, evidence_summary
    
    def _detect_keywords(self, text: str):
        """Detect standard-specific keywords."""
        # GAAP keywords
        for keyword in self.GAAP_INDICATORS['keywords']:
            count = len(re.findall(re.escape(keyword), text))
            if count > 0:
                self.detection_scores['gaap'] += count * 2
                self.evidence['gaap'].append(f"Keyword '{keyword}' found {count} times")
        
        # IFRS keywords
        for keyword in self.IFRS_INDICATORS['keywords']:
            count = len(re.findall(re.escape(keyword), text))
            if count > 0:
                self.detection_scores['ifrs'] += count * 2
                self.evidence['ifrs'].append(f"Keyword '{keyword}' found {count} times")
    
    def _detect_statement_names(self, text: str):
        """Detect standard-specific statement names."""
        # GAAP statement names
        for name in self.GAAP_INDICATORS['statement_names']:
            if name in text:
                self.detection_scores['gaap'] += 5
                self.evidence['gaap'].append(f"Statement name: '{name}'")
        
        # IFRS statement names
        for name in self.IFRS_INDICATORS['statement_names']:
            if name in text:
                self.detection_scores['ifrs'] += 5
                self.evidence['ifrs'].append(f"Statement name: '{name}'")
    
    def _detect_line_items(self, text: str):
        """Detect standard-specific line items."""
        # GAAP line items
        for item in self.GAAP_INDICATORS['line_items']:
            if item in text:
                self.detection_scores['gaap'] += 3
                self.evidence['gaap'].append(f"Line item: '{item}'")
        
        # IFRS line items
        for item in self.IFRS_INDICATORS['line_items']:
            if item in text:
                self.detection_scores['ifrs'] += 3
                self.evidence['ifrs'].append(f"Line item: '{item}'")
    
    def _detect_policies(self, text: str):
        """Detect accounting policy indicators."""
        # GAAP policies
        for policy in self.GAAP_INDICATORS['policies']:
            if policy in text:
                self.detection_scores['gaap'] += 4
                self.evidence['gaap'].append(f"Policy: '{policy}'")
        
        # IFRS policies
        for policy in self.IFRS_INDICATORS['policies']:
            if policy in text:
                self.detection_scores['ifrs'] += 4
                self.evidence['ifrs'].append(f"Policy: '{policy}'")
    
    def _detect_regulatory_refs(self, text: str):
        """Detect regulatory body references."""
        # GAAP regulatory bodies
        gaap_bodies = ['sec', 'fasb', 'pcaob', 'aicpa']
        for body in gaap_bodies:
            count = len(re.findall(r'\b' + body + r'\b', text))
            if count > 0:
                self.detection_scores['gaap'] += count * 1.5
                self.evidence['gaap'].append(f"Regulatory body '{body.upper()}' mentioned {count} times")
        
        # IFRS regulatory bodies
        ifrs_bodies = ['iasb', 'ifric', 'ias']
        for body in ifrs_bodies:
            count = len(re.findall(r'\b' + body + r'\b', text))
            if count > 0:
                self.detection_scores['ifrs'] += count * 1.5
                self.evidence['ifrs'].append(f"Regulatory body '{body.upper()}' mentioned {count} times")
    
    def get_key_differences(self, standard: AccountingStandard) -> Dict[str, str]:
        """
        Get key accounting differences for the detected standard.
        
        Args:
            standard: Detected accounting standard
            
        Returns:
            Dictionary of key differences
        """
        if standard == AccountingStandard.GAAP:
            return {
                'inventory_valuation': 'LIFO, FIFO, or Weighted Average allowed',
                'development_costs': 'Expensed as incurred (R&D)',
                'ppe_valuation': 'Historical cost model only',
                'impairment_reversal': 'Not permitted',
                'extraordinary_items': 'Allowed (pre-2015)',
                'statement_names': 'Statement of Operations, Balance Sheet',
                'revaluation': 'Not permitted for PPE',
                'functional_currency': 'Less emphasis'
            }
        elif standard == AccountingStandard.IFRS:
            return {
                'inventory_valuation': 'FIFO or Weighted Average (LIFO prohibited)',
                'development_costs': 'Capitalized if criteria met',
                'ppe_valuation': 'Historical cost or Revaluation model',
                'impairment_reversal': 'Permitted under certain conditions',
                'extraordinary_items': 'Prohibited',
                'statement_names': 'Statement of Comprehensive Income, Statement of Financial Position',
                'revaluation': 'Revaluation model available for PPE',
                'functional_currency': 'Explicitly defined'
            }
        else:
            return {}
    
    def suggest_adjustments(self, standard: AccountingStandard) -> List[str]:
        """
        Suggest potential adjustments needed for reconciliation.
        
        Args:
            standard: Detected accounting standard
            
        Returns:
            List of suggested adjustments
        """
        if standard == AccountingStandard.GAAP:
            return [
                "Check for LIFO inventory valuation (not allowed in IFRS)",
                "Review R&D expenses (may be capitalized in IFRS)",
                "Examine PPE for potential revaluation (IFRS allows)",
                "Review impairment losses (IFRS allows reversals)",
                "Check classification of extraordinary items"
            ]
        elif standard == AccountingStandard.IFRS:
            return [
                "Review capitalized development costs (expensed in GAAP)",
                "Check for PPE revaluations (not in GAAP)",
                "Examine impairment reversals (not allowed in GAAP)",
                "Review OCI items and reclassifications",
                "Check functional currency disclosures"
            ]
        else:
            return ["Unable to determine standard - manual review required"]


# Example usage
if __name__ == "__main__":
    classifier = GaapIfrsClassifier()
    
    # Example text from a GAAP report
    gaap_text = """
    The consolidated financial statements have been prepared in accordance with 
    generally accepted accounting principles in the United States (US GAAP) and 
    the rules and regulations of the Securities and Exchange Commission (SEC).
    
    We use the LIFO method for inventory valuation. Research and development 
    costs are expensed as incurred. Property, plant and equipment are stated 
    at historical cost.
    """
    
    standard, confidence, evidence = classifier.classify(gaap_text)
    print(f"Standard: {standard.value}")
    print(f"Confidence: {confidence:.2%}")
    print(f"Evidence: {evidence}")
