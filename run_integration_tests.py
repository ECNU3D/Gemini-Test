import os
import sys
import importlib
import traceback
import asyncio  # Add asyncio import
import inspect # Add inspect import

# Define the directory containing the example scripts
EXAMPLES_DIR = "openai_compatible_examples/advanced_usage"

# Add the example directory and its parent to sys.path 
# to allow imports within the examples and their utils
script_dir = os.path.dirname(os.path.abspath(__file__))
examples_path = os.path.join(script_dir, EXAMPLES_DIR)
parent_examples_path = os.path.dirname(examples_path)

sys.path.insert(0, examples_path)
sys.path.insert(0, parent_examples_path)

def run_all_examples():
    """Runs the main() function from each Python script in the EXAMPLES_DIR."""
    success_count = 0
    fail_count = 0
    failed_scripts = []

    print(f"--- Running Integration Tests for scripts in {EXAMPLES_DIR} ---")

    # List all python files in the directory, excluding __init__.py
    try:
        all_files = os.listdir(examples_path)
        script_files = [f for f in all_files if f.endswith(".py") and f != "__init__.py"]
    except FileNotFoundError:
        print(f"Error: Examples directory not found at {examples_path}")
        return

    for filename in script_files:
        module_name = filename[:-3] # Remove .py extension
        full_module_path = f"{EXAMPLES_DIR.replace('/.', '').replace('/', '.')}.{module_name}"
        
        print(f"\n--- Running: {filename} ---")
        try:
            # Import the module dynamically
            module = importlib.import_module(full_module_path)

            # Check if the module has a main function
            if hasattr(module, 'main') and callable(module.main):
                # Check if main is an async function
                if inspect.iscoroutinefunction(module.main):
                    asyncio.run(module.main()) # Run async main
                else:
                    module.main() # Run sync main
                print(f"--- Success: {filename} completed successfully. ---")
                success_count += 1
            else:
                print(f"--- Skipped: {filename} (No main function found) ---")

        except Exception as e:
            print(f"--- Failed: {filename} encountered an error --- ")
            print(traceback.format_exc()) # Print detailed traceback
            print(f"Error Type: {type(e).__name__}, Message: {e}")
            print("--------------------------------------------------")
            fail_count += 1
            failed_scripts.append(filename)

    print("\n--- Integration Test Summary ---")
    print(f"Total scripts found: {len(script_files)}")
    print(f"Successfully executed: {success_count}")
    print(f"Failed: {fail_count}")
    if failed_scripts:
        print(f"Failed scripts: {', '.join(failed_scripts)}")
    print("---------------------------------")

if __name__ == "__main__":
    # Ensure environment variables (like OPENAI_API_BASE, API keys) 
    # are set correctly before running this script.
    # You might need a .env file either in the root or the example directory.
    print("Important: Ensure your .env file is configured correctly with API base, model, and credentials.")
    run_all_examples() 