
import os
from typing import List, Optional
from loguru import logger

try:
    from huggingface_hub import InferenceClient
except ImportError:
    InferenceClient = None

try:
    import torch
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

class FinancialSummarizer:
    """
    Generates high-quality summaries and risk extraction using AI models.
    Uses Hugging Face Inference API for speed and reliability, with local fallback.
    """
    
    # Model specialized for summarization
    SUMMARY_MODEL = "facebook/bart-large-cnn"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.use_api = bool(api_key and InferenceClient)
        self.local_pipeline = None
        
        if self.use_api:
            logger.info("Initialized FinancialSummarizer with HF API.")
            self.client = InferenceClient(provider="hf-inference", api_key=api_key)
        else:
            logger.info("Initialized FinancialSummarizer in Local Mode (transformers).")
            if not TRANSFORMERS_AVAILABLE:
                logger.warning("Transformers not installed. Local summary unavailable.")

    def _load_local_model(self):
        """Lazy load local summarization pipeline."""
        # Safety check for Streamlit Cloud
        is_streamlit_cloud = os.environ.get("STREAMLIT_RUNTIME_ENV") == "cloud" or os.environ.get("HOSTNAME", "").startswith("streamlit")
        
        if is_streamlit_cloud and not self.api_key:
            logger.warning("Running on Streamlit Cloud without API key. Skipping local BART summarizer to prevent crash.")
            return

        if not self.local_pipeline and TRANSFORMERS_AVAILABLE:
            logger.info(f"Loading local summarization model: {self.SUMMARY_MODEL}")
            try:
                # Use a slightly smaller model locally if possible, but keep BART as default
                self.local_pipeline = pipeline("summarization", model=self.SUMMARY_MODEL, device=-1) # Force CPU for stability
            except Exception as e:
                logger.error(f"Failed to load local model: {e}")

    def summarize(self, text: str, max_length: int = 150) -> str:
        """Summarize financial text into analytical bullet points."""
        if not text:
            return "No text provided for summarization."
            
        # Refined strategy: Skip first ~2500 chars if they look like legal cover page
        analytical_text = text
        if "Indicate by check mark" in text[:3000] or "Registrant" in text[:3000]:
            analytical_text = text[3000:7000]
        else:
            analytical_text = text[:4000]

        prompt = (
            "Summarize the following financial results into 3-4 professional bullet points. "
            f"TEXT: {analytical_text}"
        )
        
        if self.use_api:
            try:
                result = self.client.summarization(prompt, model=self.SUMMARY_MODEL, min_length=50, max_length=max_length)
                return result.summary_text
            except Exception as e:
                logger.error(f"API Summarization failed: {e}. Falling back to local.")

        # Local Fallback
        self._load_local_model()
        if self.local_pipeline:
            try:
                # Dynamic length adjustment to avoid "index out of range"
                input_len = len(prompt.split())
                adj_max = min(max_length, max(20, int(input_len * 0.8)))
                adj_min = min(50, int(adj_max * 0.5))
                
                result = self.local_pipeline(prompt, max_length=adj_max, min_length=adj_min, do_sample=False)
                return result[0]['summary_text']
            except Exception as e:
                logger.error(f"Local summarization failed: {e}")
                return "Error generating local AI summary."
        
        return "AI Summary unavailable."

    def extract_risks(self, text: str) -> List[str]:
        """Extract key business risks."""
        if not text:
            return ["No text provided."]
            
        risk_text = text[:3000]
        prompt = f"Extract top 3 financial risks: {risk_text}"
        
        if self.use_api:
            try:
                result = self.client.summarization(prompt, model=self.SUMMARY_MODEL, max_length=100)
                return [r.strip() for r in result.summary_text.split('.') if len(r) > 10][:3]
            except Exception as e:
                logger.error(f"API Risk extraction failed: {e}. Falling back to local.")

        self._load_local_model()
        if self.local_pipeline:
            try:
                input_len = len(prompt.split())
                adj_max = min(100, max(20, int(input_len * 0.6)))
                result = self.local_pipeline(prompt, max_length=adj_max, min_length=10, do_sample=False)
                summary = result[0]['summary_text']
                return [r.strip() for r in summary.split('.') if len(r) > 10][:3]
            except Exception as e:
                logger.error(f"Local risk extraction failed: {e}")
                return ["Error extracting local risks."]
        
        return ["Risk extraction unavailable."]

    def generate_executive_narrative(self, model, ai_summary: str) -> str:
        """Synthesizes results into a professional investment narrative."""
        latest_inc = model.historical_income_statements[-1]
        margin = model.assumptions.operating_margin
        rec = model.recommendation
        target = model.target_price
        upside = model.upside_potential or 0
        
        prompt = (
            f"Provide a 3-sentence investment narrative for {model.company_name}. "
            f"Revenue: ${latest_inc.revenue:,.0f}, Margin: {margin:.1%}, Rating: {rec}, Target: ${target:,.2f} ({upside:+.1%}). "
            f"Findings: {ai_summary[:300]}"
        )
        
        if self.use_api:
            try:
                result = self.client.summarization(prompt, model=self.SUMMARY_MODEL, max_length=200)
                return result.summary_text
            except Exception as e:
                logger.error(f"API Narrative failed: {e}. Falling back to local.")

        self._load_local_model()
        if self.local_pipeline:
            try:
                input_len = len(prompt.split())
                adj_max = min(200, max(40, int(input_len * 0.9)))
                result = self.local_pipeline(prompt, max_length=adj_max, min_length=30, do_sample=False)
                return result[0]['summary_text']
            except Exception as e:
                logger.error(f"Local narrative failed: {e}")
                return "Error generating local narrative."

        return "Investment narrative could not be generated."

if __name__ == "__main__":
    # Test
    summarizer = FinancialSummarizer(api_key=os.getenv("HF_TOKEN"))
    test_text = "NVIDIA today reported revenue for the fourth quarter ended January 26, 2025, of $22.1 billion, up 22% from the previous quarter and up 265% from a year ago. For the full year, revenue was up 126% to $60.9 billion. GAAP earnings per diluted share for the quarter were $4.93, up 33% from the previous quarter and up 765% from a year ago."
    print(summarizer.summarize(test_text))
