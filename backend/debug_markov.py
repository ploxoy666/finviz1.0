
import sys
import os
import traceback

# Setup paths
BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)

print(f"Testing from: {BASE_DIR}")

# Add the markov app directory to sys.path
MARKOV_DIR = os.path.join(BASE_DIR, "finanalyzer", "markov")
if MARKOV_DIR not in sys.path:
    sys.path.append(MARKOV_DIR)
    print(f"Added {MARKOV_DIR} to sys.path")

try:
    print("Attempting imports...")
    from finanalyzer.core.markov_integration import run_markov_chain_analysis
    print("Import successful. Running analysis for SPY...")
    
    # Run a quick test
    console_output, predictions, hist_data, viz, discretizer, model = run_markov_chain_analysis(
        "SPY", "1y", 3, "returns", 1
    )
    
    print("\n--- Analysis Result ---")
    if predictions:
        print("Success!")
    else:
        print("Failed.")
        print("\n--- Console Output (Log) ---")
        print(console_output)

except Exception as e:
    print(f"\nCRITICAL ERROR: {e}")
    traceback.print_exc()
