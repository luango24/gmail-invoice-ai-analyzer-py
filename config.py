import json
import os

# Load Configuration
def load_config():
    config_path = "config.json"
    if not os.path.exists(config_path):
        print(f"Config file not found: {config_path}")
        return {
            "pdf_directory": "pdfInvoices", 
            "ollama_model": "llama3.2",
            "DownloadInvoice": False,
            "SecretJsonFile": ""
        }
    with open(config_path, 'r') as f:
        return json.load(f)

CONFIG = load_config()
