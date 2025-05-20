"""
Example of using the OpenAI-compatible Chat Completions endpoint with
'presence_penalty' and 'frequency_penalty' parameters using the official
'openai' Python SDK.

Demonstrates how to discourage the model from repeating tokens or topics.
"""

import os
import sys
from dotenv import load_dotenv
from openai import OpenAI, APIError, APITimeoutError, RateLimitError
import re # For Zappy-Zap counting and Part B extraction
from collections import Counter # For TTR and bigram counting

# Add the parent directory (openai_compatible_examples) to sys.path
# to allow importing from the 'utils' module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils.auth_helpers import get_api_key

# --- Helper Functions for Quantification ---
def calculate_ttr(text: str) -> float:
    """Calculates the Token-level Type-Token Ratio (TTR)."""
    if not text:
        return 0.0
    tokens = re.findall(r'\w+', text.lower()) # Simple word tokenization
    if not tokens:
        return 0.0
    unique_tokens = set(tokens)
    return len(unique_tokens) / len(tokens)

def count_zappy_zap(text: str) -> int:
    """Counts exact occurrences of 'Zappy-Zap'."""
    return len(re.findall(r'Zappy-Zap', text)) # Case-sensitive as per prompt

def extract_part_b(text: str) -> str:
    """Extracts Part B (slogan list) from the response."""
    match = re.search(r'\*\*Part B – Brain-storming playground\*\*(.*)', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""

def count_duplicate_bigrams_in_slogans(slogan_text: str) -> int:
    """Counts the number of unique bigrams that are duplicated in the slogan list."""
    if not slogan_text:
        return 0
    slogans = [s.strip() for s in slogan_text.split('\\n') if s.strip()]
    all_bigrams = []
    for slogan in slogans:
        words = re.findall(r'\w+', slogan.lower())
        if len(words) >= 2:
            bigrams = list(zip(words, words[1:]))
            all_bigrams.extend(bigrams)
    
    if not all_bigrams:
        return 0
    
    bigram_counts = Counter(all_bigrams)
    duplicate_bigram_types_count = 0
    for bigram, count in bigram_counts.items():
        if count > 1:
            duplicate_bigram_types_count += 1
    return duplicate_bigram_types_count

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

# Get endpoint and API key from environment variables
API_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key")
MODEL_NAME = os.getenv("MODEL_NAME") # Optional: If endpoint supports model selection

# --- Initialize OpenAI Client ---
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=API_KEY,
)

# --- Presence and Frequency Penalty Explanation ---
# These penalties modify the likelihood of tokens appearing based on their presence
# or frequency in the generated text so far.
# Both range from -2.0 to 2.0. Higher positive values increase the penalty.
# Negative values would encourage token repetition (less common use case).

# Presence Penalty:
# - Positive values penalize new tokens based on whether they have appeared in the
#   text so far, increasing the model's likelihood to talk about new topics.
# - A value of 0 means no penalty.
# - Useful for discouraging topic repetition and encouraging more diverse output.

# Frequency Penalty:
# - Positive values penalize new tokens based on their existing frequency in the
#   text so far, decreasing the model's likelihood to repeat the same line verbatim.
# - A value of 0 means no penalty.
# - Useful for reducing word-level repetition, making text less monotonous.

# --- API Request Function ---
def generate_completion_with_penalties(
    prompt_content: str,
    presence_val: float = 0.0,
    frequency_val: float = 0.0,
    temp: float = 0.7 # Keep temperature consistent for comparison
):
    """Generates a completion with specified presence and frequency penalties."""
    messages = [
        {"role": "user", "content": prompt_content}
    ]

    # print(f"--- Sending request with Presence Penalty: {presence_val}, Frequency Penalty: {frequency_val}, Temp: {temp} ---")
    # print(f'Prompt: "{prompt_content}"')
    # print("-" * 30) # Moved detailed print to the main loop for run-specific logging

    assistant_message_content = None # Initialize to None

    try:
        client.api_key = get_api_key()
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temp,
            presence_penalty=presence_val,
            frequency_penalty=frequency_val,
            max_tokens=350, # Increased max_tokens for the longer prompt
            n=1
        )

        assistant_message_content = completion.choices[0].message.content
        # print(f"Assistant (PP: {presence_val}, FP: {frequency_val}):") # Moved detailed print
        # print(assistant_message_content)

    except (APIError, RateLimitError, APITimeoutError) as e:
        print(f"An API error occurred (PP: {presence_val}, FP: {frequency_val}): {e}")
        if hasattr(e, 'status_code'):
            print(f"Status Code: {e.status_code}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                print(f"Response Body: {e.response.text}")
            except Exception:
                 print("Could not print response body.")
        elif hasattr(e, 'message'):
            print(f"Error Message: {e.message}")

    except KeyError as e:
        print(f"Error accessing key in API response (PP: {presence_val}, FP: {frequency_val}): {e}")
    except Exception as e:
        print(f"An unexpected error occurred (PP: {presence_val}, FP: {frequency_val}): {e}")
        print(f"Type: {type(e)}")
    # finally: # Moved detailed print
        # print("-" * 30)
        # print("\\n")
    
    return assistant_message_content

# --- Main Execution ---
if __name__ == "__main__":
    user_prompt = """You are a playful copy-writer.

**Part A – Repetition playground**  
Write a 120-word product pitch for a fictional energy drink called "Zappy-Zap."  
• Mention the brand name exactly **10 times**.  
• End every sentence with the word **"power."**

**Part B – Brain-storming playground**  
Now list **20 completely different slogan ideas**, one per line, for the same drink.  
• Each slogan must be ≤ 6 words.  
• Do **not** reuse any word that has already appeared in Part B (except unavoidable stop-words like "the", "a", "and").  

Return Parts A and B in that order. Do not add anything else."""

    fixed_temperature = 0.7
    print(f"--- Demonstrating Penalties with Test Harness & Quantification (Temp: {fixed_temperature}) ---")

    frequency_penalty_values = [0.0, 0.4, 0.8, 1.2]
    presence_penalty_values = [0.0, 0.4, 0.8, 1.2]
    num_runs_per_setting = 5

    all_run_metrics = [] 

    for fp_val in frequency_penalty_values:
        for pp_val in presence_penalty_values:
            print(f"\n>>> Testing Setting: FP={fp_val}, PP={pp_val} <<<")
            print("-" * 50)

            for run_num in range(1, num_runs_per_setting + 1):
                print(f"\n--- Run {run_num}/{num_runs_per_setting} for FP={fp_val}, PP={pp_val} ---")
                
                print(f"Sending request with Presence Penalty: {pp_val}, Frequency Penalty: {fp_val}, Temp: {fixed_temperature}")
                print("-" * 30)

                assistant_response = generate_completion_with_penalties(
                    prompt_content=user_prompt,
                    presence_val=pp_val,
                    frequency_val=fp_val,
                    temp=fixed_temperature
                )

                ttr, zappy_zap_count, duplicate_bigrams = -1.0, -1, -1 # Default/error values

                if assistant_response:
                    print("\nAssistant's Full Response:")
                    print(assistant_response)
                    print("-" * 30)

                    ttr = calculate_ttr(assistant_response)
                    zappy_zap_count = count_zappy_zap(assistant_response)
                    part_b_text = extract_part_b(assistant_response)
                    
                    if not part_b_text:
                        print("  Part B (slogans) not found in response.")
                        duplicate_bigrams = 0 
                    else:
                        duplicate_bigrams = count_duplicate_bigrams_in_slogans(part_b_text)
                    
                    print(f"Metrics for Run {run_num}:")
                    print(f"  Token-level TTR: {ttr:.4f}")
                    print(f"  'Zappy-Zap' count: {zappy_zap_count}")
                    print(f"  Duplicate bigram types in slogans (Part B): {duplicate_bigrams}")
                else:
                    print(f"Metrics for Run {run_num}: No response received or error occurred.")
                
                all_run_metrics.append({
                    "fp": fp_val,
                    "pp": pp_val,
                    "run": run_num,
                    "ttr": ttr,
                    "zappy_zap_count": zappy_zap_count,
                    "duplicate_bigrams": duplicate_bigrams
                })
                
                print("-" * 30)
            print(f"\nCompleted {num_runs_per_setting} runs for FP={fp_val}, PP={pp_val}")
            print("=" * 50 + "\n")

    # --- Print and Save Individual Run Metrics Table (as before) ---
    print("\n--- Overall Metrics Summary Table (Individual Runs - Console) ---")
    console_header_individual = f"{'FP':<5} | {'PP':<5} | {'Run':<4} | {'TTR':<7} | {'ZappyZap':<10} | {'DupBigrams':<12}"
    print(console_header_individual)
    print("-" * len(console_header_individual))
    for metrics in all_run_metrics:
        print(f"{metrics['fp']:<5.1f} | {metrics['pp']:<5.1f} | {metrics['run']:<4} | "
              f"{metrics['ttr']:.4f} | {metrics['zappy_zap_count']:<10} | {metrics['duplicate_bigrams']:<12}")

    md_table_individual_lines = [] 
    md_header_individual = "| FP    | PP    | Run | TTR    | ZappyZap | DupBigrams   |"
    md_separator_individual = "|-------|-------|-----|--------|----------|--------------|"
    md_table_individual_lines.append(md_header_individual)
    md_table_individual_lines.append(md_separator_individual)
    for metrics in all_run_metrics:
        row = f"| {metrics['fp']:<5.1f} | {metrics['pp']:<5.1f} | {metrics['run']:<3} | " \
              f"{metrics['ttr']:.4f} | {metrics['zappy_zap_count']:<8} | {metrics['duplicate_bigrams']:<12} |"
        md_table_individual_lines.append(row)
    
    # --- Aggregate and Calculate Averaged Metrics ---
    aggregated_penalty_metrics = {}
    for m in all_run_metrics:
        key = (m['fp'], m['pp'])
        if key not in aggregated_penalty_metrics:
            aggregated_penalty_metrics[key] = {
                'ttr_sum': 0.0, 'ttr_valid_runs': 0,
                'zappy_sum': 0, 'zappy_valid_runs': 0,
                'bigram_sum': 0, 'bigram_valid_runs': 0
            }
        
        if m['ttr'] != -1.0:
            aggregated_penalty_metrics[key]['ttr_sum'] += m['ttr']
            aggregated_penalty_metrics[key]['ttr_valid_runs'] += 1
        if m['zappy_zap_count'] != -1:
            aggregated_penalty_metrics[key]['zappy_sum'] += m['zappy_zap_count']
            aggregated_penalty_metrics[key]['zappy_valid_runs'] += 1
        if m['duplicate_bigrams'] != -1:
            aggregated_penalty_metrics[key]['bigram_sum'] += m['duplicate_bigrams']
            aggregated_penalty_metrics[key]['bigram_valid_runs'] += 1

    averaged_metrics_data = []
    for key, sums in aggregated_penalty_metrics.items():
        avg_ttr = sums['ttr_sum'] / sums['ttr_valid_runs'] if sums['ttr_valid_runs'] > 0 else 0.0
        avg_zappy = sums['zappy_sum'] / sums['zappy_valid_runs'] if sums['zappy_valid_runs'] > 0 else 0.0
        avg_bigram = sums['bigram_sum'] / sums['bigram_valid_runs'] if sums['bigram_valid_runs'] > 0 else 0.0
        averaged_metrics_data.append({
            'fp': key[0], 'pp': key[1],
            'avg_ttr': avg_ttr,
            'avg_zappy_zap': avg_zappy,
            'avg_duplicate_bigrams': avg_bigram,
            'runs_for_avg': f"{sums['ttr_valid_runs']}/{num_runs_per_setting}" # Show how many runs contributed
        })

    # --- Print and Save Averaged Metrics Table ---
    print("\n--- Averaged Metrics Summary Table (Console) ---")
    console_header_avg = f"{'FP':<5} | {'PP':<5} | {'Avg TTR':<10} | {'Avg ZappyZap':<13} | {'Avg DupBigrams':<15} | {'Valid Runs':<10}"
    print(console_header_avg)
    print("-" * len(console_header_avg))
    for avg_m in averaged_metrics_data:
        print(f"{avg_m['fp']:<5.1f} | {avg_m['pp']:<5.1f} | {avg_m['avg_ttr']:<10.4f} | "
              f"{avg_m['avg_zappy_zap']:<13.2f} | {avg_m['avg_duplicate_bigrams']:<15.2f} | {avg_m['runs_for_avg']:<10}")

    md_table_averaged_lines = []
    md_header_avg = "| FP    | PP    | Avg TTR   | Avg ZappyZap | Avg DupBigrams | Valid Runs   |"
    md_separator_avg = "|-------|-------|-----------|--------------|----------------|--------------|"
    md_table_averaged_lines.append(md_header_avg)
    md_table_averaged_lines.append(md_separator_avg)
    for avg_m in averaged_metrics_data:
        row = f"| {avg_m['fp']:<5.1f} | {avg_m['pp']:<5.1f} | {avg_m['avg_ttr']:<9.4f} | " \
              f"{avg_m['avg_zappy_zap']:<12.2f} | {avg_m['avg_duplicate_bigrams']:<14.2f} | {avg_m['runs_for_avg']:<12} |"
        md_table_averaged_lines.append(row)

    # --- Write both tables to Markdown file ---
    output_filename = "metrics_summary.md"
    try:
        with open(output_filename, 'w') as f:
            f.write("## Overall Metrics Summary (Individual Runs)\n\n")
            f.write("\n".join(md_table_individual_lines))
            f.write("\n\n")
            f.write("## Averaged Metrics Summary (Per FP/PP Setting)\n\n")
            f.write("\n".join(md_table_averaged_lines))
            f.write("\n\n")
        print(f"\nMarkdown summary tables saved to: {output_filename}")
    except IOError as e:
        print(f"\nError writing Markdown file {output_filename}: {e}")

    # --- Generate and Save Plots ---
    plots_saved = False
    try:
        import matplotlib.pyplot as plt
        
        # Helper function to prepare data for plotting for a specific metric
        def get_plot_data(metric_name_in_data):
            plot_series = {}
            # presence_penalty_values is already defined earlier
            for pp_val in sorted(list(set(m['pp'] for m in averaged_metrics_data))):
                series_data = []
                for m_point in sorted(averaged_metrics_data, key=lambda x: x['fp']):
                    if m_point['pp'] == pp_val:
                        series_data.append((m_point['fp'], m_point[metric_name_in_data]))
                if series_data:
                    fps, metric_values = zip(*series_data)
                    plot_series[pp_val] = {'fps': fps, 'metric_values': metric_values}
            return plot_series

        # Plot 1: Average TTR vs Frequency Penalty
        plt.figure(figsize=(10, 6))
        ttr_plot_data = get_plot_data('avg_ttr')
        for pp_val, data in ttr_plot_data.items():
            plt.plot(data['fps'], data['metric_values'], marker='o', linestyle='-', label=f'PP = {pp_val}')
        plt.title('Average TTR vs Frequency Penalty (lines for Presence Penalty)')
        plt.xlabel('Frequency Penalty (FP)')
        plt.ylabel('Average Type-Token Ratio (TTR)')
        plt.xticks(frequency_penalty_values) # Ensure all FP values are shown as ticks
        plt.legend()
        plt.grid(True)
        plt.savefig("avg_ttr_vs_fp_plot.png")
        plt.close()
        print("\nPlot 'avg_ttr_vs_fp_plot.png' saved.")

        # Plot 2: Average ZappyZap Count vs Frequency Penalty
        plt.figure(figsize=(10, 6))
        zappy_plot_data = get_plot_data('avg_zappy_zap')
        for pp_val, data in zappy_plot_data.items():
            plt.plot(data['fps'], data['metric_values'], marker='s', linestyle='--', label=f'PP = {pp_val}')
        plt.title('Average \'Zappy-Zap\' Count vs Frequency Penalty')
        plt.xlabel('Frequency Penalty (FP)')
        plt.ylabel('Average \'Zappy-Zap\' Count')
        plt.xticks(frequency_penalty_values)
        plt.legend()
        plt.grid(True)
        plt.savefig("avg_zappy_zap_vs_fp_plot.png")
        plt.close()
        print("Plot 'avg_zappy_zap_vs_fp_plot.png' saved.")

        # Plot 3: Average Duplicate Bigrams vs Frequency Penalty
        plt.figure(figsize=(10, 6))
        bigram_plot_data = get_plot_data('avg_duplicate_bigrams')
        for pp_val, data in bigram_plot_data.items():
            plt.plot(data['fps'], data['metric_values'], marker='^', linestyle=':', label=f'PP = {pp_val}')
        plt.title('Average Duplicate Bigrams (Part B) vs Frequency Penalty')
        plt.xlabel('Frequency Penalty (FP)')
        plt.ylabel('Average Duplicate Bigrams in Slogans')
        plt.xticks(frequency_penalty_values)
        plt.legend()
        plt.grid(True)
        plt.savefig("avg_dup_bigrams_vs_fp_plot.png")
        plt.close()
        print("Plot 'avg_dup_bigrams_vs_fp_plot.png' saved.")
        plots_saved = True

    except ImportError:
        print("\nMatplotlib library not found. Skipping plot generation.")
        print("To generate plots, please install it: pip install matplotlib")
    except Exception as e:
        print(f"\nAn error occurred during plot generation: {e}")

    if plots_saved:
        print("\nAll plots saved successfully.")

    print("\nAll test runs for presence and frequency penalties with quantification are complete.")
    print("Review the outputs for each (FP, PP) combination, individual runs, averaged results, and generated plots.")
    print(f"Temperature was held constant at {fixed_temperature}.") 