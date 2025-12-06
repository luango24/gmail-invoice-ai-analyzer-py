# Supermarket Invoice AI Analyzer (Python Version)

This project automatically downloads supermarket invoices from Gmail, extracts line items using PDF parsing, and uses a local AI model (Ollama) to categorize items and generate spending insights.

## Features

- **Gmail Integration**: Automatically searches for and downloads invoice PDFs.
- **PDF Parsing**: Extracts date, supermarket name, total, and line items.
- **Auto-Categorization**: Uses a hybrid approach (Keywords + Local AI Fallback) to categorize items.
- **AI Analysis**: Generates an executive summary and strategic recommendations using DeepSeek/Llama via Ollama.
- **Dashboard**: Generates an HTML dashboard to visualize spending.

## Prerequisites

1.  **Python 3.8+**
2.  **Ollama**: Installed and running locally (`ollama serve`).
    - Recommended model: `llama3.2` or `deepseek-r1`.
3.  **Gmail API Credentials**:
    - Create a project in Google Cloud Console.
    - Enable the Gmail API.
    - Create OAuth Desktop credentials and download `credentials.json`.

## Setup

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure the project:
    - Copy `config.example.json` to `config.json`.
    - Update the paths and query string in `config.json`.
    ```json
    {
        "pdf_directory": "./invoices",
        "ollama_model": "llama3.2",
        "SecretJsonFile": "path/to/credentials.json",
        "DownloadInvoice": true,
        "QueryString": "from:(Super 99) has:attachment"
    }
    ```

## Usage

Run the main script:
```bash
python main.py
```

On the first run, it will open a browser window to authenticate with Google.

## License

MIT
