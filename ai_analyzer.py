import sys
import subprocess
from config import CONFIG

def check_model_availability(model_name):
    print(f"Checking for Ollama model: {model_name}...")
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)
        if model_name not in result.stdout:
            print(f"Error: Model '{model_name}' not found. Please run 'ollama pull {model_name}'")
            return False
        return True
    except FileNotFoundError:
        print("Error: Ollama not installed or not in PATH.")
        return False
    except Exception as e:
        print(f"Error checking model: {e}")
        return False

def analyze_aggregated_data(aggregated_categories, total_spend):
    print("\n--- RUNNING OLLAMA AGGREGATED ANALYSIS ---\n")
    
    category_summary = "\n".join([f"- {cat}: ${amount:.2f}" for cat, amount in aggregated_categories.items()])
    
    prompt_data = (
        f"Total Spending: ${total_spend:.2f}\n"
        f"Category Breakdown:\n{category_summary}\n"
    )
    
    prompt = (
        "You are an expert financial assistant. Analyze the following aggregated expense data:\n\n"
        f"{prompt_data}\n\n"
        "Please provide a high-level **Executive Dashboard Summary** and 3 key **Strategic Recommendations** to optimize the budget."
        "Format using Markdown."
    )
    
    try:
        process = subprocess.Popen(
            ["ollama", "run", CONFIG["ollama_model"]],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            # errors='replace' # Handle potential encoding issues
        )
        stdout, stderr = process.communicate(input=prompt)
        if process.returncode != 0:
            return f"Error: {stderr}"
        return stdout
            
    except Exception as e:
        return f"Failed to run analysis: {e}"

def categorize_item_with_ai(description):
    # print(f"AI Categorizing: {description}...") # Optional debug
    prompt = (
        f"Categorize the following supermarket item into exactly one of these categories: "
        "Proteins, Vegetables, Fruits, Dairy, Dry Food, Snacks, Hygiene, Cleaning Supplies, "
        "Pet Supplies, Frozen, Drinks, Canned Goods, Bakery, Baby, Cereals, Sauces, Other.\n"
        f"Item: {description}\n"
        "Reply ONLY with the category name. Do not add any punctuation or extra text."
    )
    
    try:
        process = subprocess.run(
            ["ollama", "run", CONFIG["ollama_model"], prompt],
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=True
        )
        category = process.stdout.strip()
        # Basic validation to ensure it returned a valid category key or reasonable string
        return category
    except Exception as e:
        print(f"AI Categorization failed: {e}")
        return "Other"
