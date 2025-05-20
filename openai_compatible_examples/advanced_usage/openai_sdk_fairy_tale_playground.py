import os
import sys
import re
import math
from collections import Counter
from openai import OpenAI
from dotenv import load_dotenv

# Attempt to import matplotlib for plotting
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Add the parent directory (openai_compatible_examples) to sys.path
# to allow importing from the 'utils' module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir) # This should be 'openai_compatible_examples'
sys.path.append(parent_dir)

from utils.auth_helpers import get_api_key

# Load environment variables from .env file
load_dotenv()

# Get API details from environment variables
api_base_url = os.getenv("OPENAI_API_BASE")
api_key = os.getenv("OPENAI_API_KEY", "dummy-key") # Default to a dummy key if not set
model_name = os.getenv("MODEL_NAME", "default-model") # Provide a default model name

if not api_base_url:
    raise ValueError("OPENAI_API_BASE environment variable not set.")

print(f"--- Configuring OpenAI SDK for Fairy Tale Playground ---")
print(f"Base URL: {api_base_url}")
print(f"Model: {model_name}")
print("API Key: Using provided key (or dummy key if not set)")
print("---")

NUM_RUNS_PER_SETTING = 3 # Number of times to run each parameter combination

# Define the fairy tale prompt
fairy_tale_prompt = (
    "Write a very short fairy tale (≤ 120 words) that must contain:\n"
    "• A talking squirrel\n"
    "• A magical gemstone\n"
    "• A sudden plot twist\n"
    "…and nothing else."
)

messages = [
    {"role": "user", "content": fairy_tale_prompt}
]

# Updated temperature and top_p ranges with 0.2 step
temperatures = [round(i * 0.2, 1) for i in range(6)] # 0.0, 0.2, ..., 1.0
top_ps = [round(i * 0.2, 1) for i in range(1, 6)]   # 0.2, 0.4, ..., 1.0

# Existing run_descriptions will largely not match; new combinations will use the default "Custom run"
run_descriptions = {
    # Original descriptions are kept but might not be hit with new ranges
    (0.2, 1.0): "A1-like: Very deterministic; almost identical every retry.",
    (0.2, 0.6): "A2-like: Same skeleton, plus strong pruning → bland wording, fewer adjectives.",
    (0.2, 0.2): "A3-like: Ultra-safe: sometimes the story stalls or repeats.",
    (0.7, 1.0): 'B1-like: "Normal creative" baseline—good variety but coherent.', # Note: 0.7 is not in the new temp list
    (1.0, 1.0): "C1-like (temp=1.0): Wild vocabulary, quirky twists.",
    (1.0, 0.6): "C2-like (temp=1.0): Energy tamed: colourful but fewer outrageous tokens.",
    (1.0, 0.2): 'C3-like (temp=1.0): "Drunk but shackled" — output can swing wildly.'
}

# --- Quantitative Metrics Helper Functions ---
def get_words(text):
    if not text: return []
    return re.findall(r'\b\w+\b', text.lower())

def get_sentences(text):
    if not text: return []
    # Split by common sentence delimiters, remove empty strings
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    return sentences

def calculate_ttr(text):
    words = get_words(text)
    if not words: return 0.0
    return len(set(words)) / len(words)

def calculate_avg_sentence_length(text):
    words = get_words(text)
    sentences = get_sentences(text)
    if not sentences: return 0.0
    return len(words) / len(sentences)

# calculate_avg_top_k_entropy function removed as logprobs are not supported by the target model/API

# --- Plotting Helper Function ---
def get_plot_data_for_metric(metric_key_name, averaged_data, x_axis_values, series_values, x_axis_data_key, series_data_key):
    plot_series = {}
    for series_val in sorted(list(set(m[series_data_key] for m in averaged_data))):
        series_data_points = []
        for x_val in sorted(x_axis_values):
            found_metric = None
            for data_point in averaged_data:
                if data_point[x_axis_data_key] == x_val and data_point[series_data_key] == series_val:
                    found_metric = data_point[metric_key_name]
                    break
            if found_metric is not None: # Only add if data exists for this x_val
                 series_data_points.append(found_metric)
            # If no data point, this x_val will be missing for this series - plot will show gap or connect over it.

        # Ensure we have x_values that correspond to the collected series_data_points
        # This filters x_axis_values to only those for which we found data for the current series_val
        current_x_values = []
        temp_series_data_points = []
        idx = 0
        for x_val in sorted(x_axis_values):
            has_data_for_x = any(dp[x_axis_data_key] == x_val and dp[series_data_key] == series_val for dp in averaged_data)
            if has_data_for_x and idx < len(series_data_points):
                current_x_values.append(x_val)
                temp_series_data_points.append(series_data_points[idx])
                idx+=1
        
        if current_x_values and temp_series_data_points:
            plot_series[series_val] = {'x_values': current_x_values, 'metric_values': temp_series_data_points}
    return plot_series

# --- Main Execution ---
def main():
    print(f"--- Starting Build-a-Fairy-Tale Playground with Metrics ({NUM_RUNS_PER_SETTING} runs per setting) ---")
    
    averaged_metrics_data = []

    try:
        client = OpenAI(
            base_url=api_base_url,
            api_key="temp-key" # Initial key, will be replaced per request
        )

        for temp in temperatures:
            for top_p_val in top_ps:
                run_id = f"{chr(ord('A') + temperatures.index(temp))}{top_ps.index(top_p_val) + 1}"
                description = run_descriptions.get((temp, top_p_val), "Custom run")

                print(f"\n--- Evaluating Setting: {run_id} ({description}) ---")
                print(f"Parameters: temperature={temp}, top_p={top_p_val}, Runs: {NUM_RUNS_PER_SETTING}")
                print("---")

                setting_ttrs = []
                setting_avg_sent_lens = []
                first_story_snippet_for_setting = "N/A"
                successful_runs_for_setting = 0

                for run_num in range(1, NUM_RUNS_PER_SETTING + 1):
                    print(f"  Run {run_num}/{NUM_RUNS_PER_SETTING} for {run_id}...")
                    client.api_key = get_api_key() # Refresh API key

                    story_content = ""
                    ttr = 0.0
                    avg_sent_len = 0.0

                    try:
                        chat_completion = client.chat.completions.create(
                            model=model_name,
                            messages=messages,
                            temperature=temp,
                            top_p=top_p_val,
                            max_tokens=160 # Approx 120 words
                            # logprobs and top_logprobs removed as they are not supported
                        )

                        if chat_completion.choices:
                            choice = chat_completion.choices[0]
                            if choice.message and choice.message.content:
                                story_content = choice.message.content
                                ttr = calculate_ttr(story_content)
                                avg_sent_len = calculate_avg_sentence_length(story_content)
                                
                                setting_ttrs.append(ttr)
                                setting_avg_sent_lens.append(avg_sent_len)
                                successful_runs_for_setting += 1

                                if run_num == 1: # Store first snippet for the table
                                    first_story_snippet_for_setting = (story_content[:70] + '...') if len(story_content) > 70 else story_content
                                
                                print(f"    Run {run_num} Metrics: TTR={ttr:.3f}, AvgSentLen={avg_sent_len:.2f}")
                                # print(f"    Story: {first_story_snippet_for_setting}") # Optional: print snippet per run
                            else:
                                print(f"    Run {run_num}: No message content found.")
                        else:
                            print(f"    Run {run_num}: No choices found in response.")
                    except Exception as e_run:
                        print(f"    Run {run_num}: Error during API call or processing: {e_run}")
                
                # Calculate averages for the setting
                avg_ttr_for_setting = sum(setting_ttrs) / len(setting_ttrs) if setting_ttrs else 0.0
                avg_avg_sent_len_for_setting = sum(setting_avg_sent_lens) / len(setting_avg_sent_lens) if setting_avg_sent_lens else 0.0

                print(f"  Setting {run_id} Averages ({successful_runs_for_setting}/{NUM_RUNS_PER_SETTING} successful runs):")
                print(f"    Avg TTR: {avg_ttr_for_setting:.3f}")
                print(f"    Avg Sentence Length: {avg_avg_sent_len_for_setting:.2f}")

                averaged_metrics_data.append({
                    'run_id': run_id,
                    'temp': temp,
                    'top_p': top_p_val,
                    'avg_ttr': avg_ttr_for_setting,
                    'avg_sent_len': avg_avg_sent_len_for_setting,
                    'avg_entropy': "N/A", # Entropy not calculated
                    'story_snippet': first_story_snippet_for_setting,
                    'successful_runs': f"{successful_runs_for_setting}/{NUM_RUNS_PER_SETTING}"
                })
                print("--- End of Setting Evaluation ---")

        md_table = "| Run ID | Temp | Top_p | Avg TTR | Avg Sent Len | Successful Runs | Story Snippet (First Run)      |\n"
        md_table += "|--------|------|-------|---------|--------------|-----------------|--------------------------------|\n"
        for data in averaged_metrics_data:
            md_table += (f"| {data['run_id']:<6} | {data['temp']:<4} | {data['top_p']:<5} | "
                         f"{data['avg_ttr']:.3f}   | {data['avg_sent_len']:<12.2f} | {data['successful_runs']:<15} | "
                         f"{data['story_snippet'].replace('|', '/').replace('\n', ' ') :<30} |")
            md_table +="\n"

        output_filename = "fairy_tale_metrics_averaged.md"
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(md_table)
        print(f"\n--- Averaged metrics table saved to {output_filename} ---")

        # --- Generate and Save Plots ---
        if MATPLOTLIB_AVAILABLE:
            plots_saved_count = 0
            try:
                # Plot 1: Average TTR vs. Temperature
                plt.figure(figsize=(10, 6))
                ttr_plot_data = get_plot_data_for_metric('avg_ttr', averaged_metrics_data, temperatures, top_ps, 'temp', 'top_p')
                for top_p_series, data in ttr_plot_data.items():
                    plt.plot(data['x_values'], data['metric_values'], marker='o', linestyle='-', label=f'Top_p = {top_p_series}')
                
                plt.title('Average TTR vs. Temperature (lines for Top_p)')
                plt.xlabel('Temperature')
                plt.ylabel('Average Type-Token Ratio (TTR)')
                plt.xticks(temperatures)
                plt.legend()
                plt.grid(True)
                plt.savefig("avg_ttr_vs_temp_plot.png")
                plt.close()
                print("Plot 'avg_ttr_vs_temp_plot.png' saved.")
                plots_saved_count += 1

                # Plot 2: Average Sentence Length vs. Temperature
                plt.figure(figsize=(10, 6))
                sent_len_plot_data = get_plot_data_for_metric('avg_sent_len', averaged_metrics_data, temperatures, top_ps, 'temp', 'top_p')
                for top_p_series, data in sent_len_plot_data.items():
                    plt.plot(data['x_values'], data['metric_values'], marker='s', linestyle='--', label=f'Top_p = {top_p_series}')
                
                plt.title('Average Sentence Length vs. Temperature (lines for Top_p)')
                plt.xlabel('Temperature')
                plt.ylabel('Average Sentence Length')
                plt.xticks(temperatures)
                plt.legend()
                plt.grid(True)
                plt.savefig("avg_sent_len_vs_temp_plot.png")
                plt.close()
                print("Plot 'avg_sent_len_vs_temp_plot.png' saved.")
                plots_saved_count += 1
                
                if plots_saved_count == 2:
                    print("\nAll plots saved successfully.")

            except Exception as e_plot:
                print(f"\nAn error occurred during plot generation: {e_plot}")
        else:
            print("\nMatplotlib library not found. Skipping plot generation.")
            print("To generate plots, please install it: pip install matplotlib")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for debugging
        raise

if __name__ == "__main__":
    main() 