import pdfplumber
import re
from datetime import datetime
import json
import glob
import os
import sys
import base64

# Gmail Imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("Warning: Google API libraries not installed. Gmail download will fail if enabled.")
    print("Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")

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

# --- GMAIL FUNCTIONS ---
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def download_gmail_attachments():
    print("Checking Gmail for new invoices...")
    creds = None
    token_path = 'token.json'
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            secret_file = CONFIG.get("SecretJsonFile")
            if not secret_file or not os.path.exists(secret_file):
                print(f"Error: SecretJsonFile not found at '{secret_file}'. Cannot authenticate.")
                return
            
            flow = InstalledAppFlow.from_client_secrets_file(secret_file, SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        
        # Query for PDF attachments
        query = 'has:attachment filename:pdf'
        # Optional: Add sender filter if configured
        # if "GmailSender" in CONFIG: query += f' from:{CONFIG["GmailSender"]}'
        
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        
        if not messages:
            print("No emails found with PDF attachments.")
            return

        print(f"Found {len(messages)} emails. Checking attachments...")
        
        pdf_dir = CONFIG["pdf_directory"]
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)

        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            
            for part in msg['payload'].get('parts', []):
                if part['filename'] and part['filename'].lower().endswith('.pdf'):
                    if 'data' in part['body']:
                        data = part['body']['data']
                    else:
                        att_id = part['body']['attachmentId']
                        att = service.users().messages().attachments().get(userId='me', messageId=message['id'], id=att_id).execute()
                        data = att['data']
                    
                    file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                    path = os.path.join(pdf_dir, part['filename'])
                    
                    # Avoid overwriting or re-downloading existing? 
                    # For now, simple check.
                    if not os.path.exists(path):
                        with open(path, 'wb') as f:
                            f.write(file_data)
                        print(f"Downloaded: {part['filename']}")
                    else:
                        print(f"Skipped (Exists): {part['filename']}")

    except Exception as e:
        print(f"An error occurred during Gmail download: {e}")

# --- INVOICE CLASSES ---

class InvoiceItem:
    def __init__(self):
        self.number = ""
        self.description = ""
        self.quantity = 0.0
        self.unit_price = 0.0
        self.discount = 0.0
        self.itbms = 0.0
        self.line_price = 0.0
        self.item_price = 0.0
        self.category = "General"

    def __str__(self):
        return (f"#{self.number}: {self.description} | Cat: {self.category} | Qty: {self.quantity} | "
                f"Unit: {self.unit_price} | Disc: {self.discount} | "
                f"Line: {self.line_price} | ITBMS: {self.itbms} | Item: {self.item_price}")

class InvoiceData:
    def __init__(self, filename=""):
        self.filename = filename
        self.supermarket = "Unknown"
        self.date = None
        self.total_amount = 0.0
        self.items = []

    def __str__(self):
        return (f"File: {self.filename}\nSupermarket: {self.supermarket}\nDate: {self.date}\nTotal: {self.total_amount}\n"
                f"Items Count: {len(self.items)}")

# --- DETECTION FUNCTIONS ---

def detect_supermarket(text):
    text_upper = text.upper()
    if "SUPER 99" in text_upper or "IMPORTADORA RICAMAR" in text_upper:
        return "Super 99"
    if "SUPERMERCADOS XTRA" in text_upper:
        return "XTRA"
    return "Unknown"

def detect_date(text):
    pattern = r'(\d{2})[/-](\d{2})[/-](\d{4})'
    for match in re.finditer(pattern, text):
        try:
            day, month, year = match.groups()
            d = datetime(int(year), int(month), int(day)).date()
            if d.year > 2000:
                return d
        except ValueError:
            continue
    return None

def detect_total(text):
    match = re.search(r'Total\s*\$?(\d+(\.\d+)?)', text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return 0.0

def categorize_item(description):
    desc_upper = description.upper()
    keywords = {
        "Proteins": ["CARNE", "POLLO", "RES", "CERDO", "PESCADO", "ATUN", "HUEVO", "PAVO", "JAMON", "SALCHICHA", "CHORIZO", "MARISCO"],
        "Vegetables": ["VEGETAL", "LECHUGA", "TOMATE", "CEBOLLA", "ZANAHORIA", "PAPA", "AGUACATE", "CILANTRO", "PIMENTON", "AJO", "PEPINO", "REPOLLO", "VERDURA", "CULANTRO", "PEREJIL", "YUKA", "OTOE", "NAME"],
        "Fruits": ["FRUTA", "MANZANA", "PERA", "UVA", "BANAN", "PLATANO", "LIMON", "NARANJA", "SANDIA", "MELON", "PAPAYA", "PINA", "GUINEO"],
        "Dairy": ["LACTEO", "LECHE", "QUESO", "YOGURT", "MANTEQUILLA", "CREMA", "MARGARINA", "QLO"],
        "Dry Food": ["ARROZ", "PASTA", "FRIJOL", "LENTEJA", "HARINA", "AZUCAR", "SAL", "ACEITE", "MENESTRA", "POROTO", "ESPAGUETI", "FIDEO", "CONDIMENTO"],
        "Snacks": ["SNACK", "PAPITA", "CHOCOLATE", "GALLETA", "DULCE", "CARAMELO", "DORITO", "CHICLE", "CROMOS"],
        "Hygiene": ["HIGIENE", "JABON", "SHAMPOO", "DESODORANTE", "PASTA DENTAL", "PAPEL HIGIENICO", "TOALLA", "CEPILLO", "ACONDICIONADOR", "PANUELO"],
        "Cleaning Supplies": ["LIMPIEZA", "DETERGENTE", "CLORO", "SUAVIZANTE", "ESCOBA", "TRAPEADOR", "DESINFECTANTE", "LAVAPLATO", "ESPONJA"],
        "Pet Supplies": ["MASCOTA", "PERRO", "GATO", "ALIMENTO", "ARENA"],
        "Frozen": ["CONGELADO", "HELADO", "HIELO"],
        "Drinks": ["BEBIDA", "JUGO", "SODA", "AGUA", "CERVEZA", "VINO", "LICOR", "GASEOSA", "REFRESCO", "RON", "WHISKY", "TE"],
        "Canned Goods": ["LATA", "CONSERVA", "MAIZ", "GUISANTE", "TUNA"],
        "Bakery": ["PAN", "MOLDE", "FLAUTA", "MICHITA", "PASTEL", "TORTA"],
        "Baby": ["BEBE", "PAÑAL", "FORMULA", "COMPOTA", "TOALLITA"],
        "Cereals": ["CEREAL", "AVENA", "GRANOLA", "CORN FLAKES"],
        "Sauces": ["SALSA", "KETCHUP", "MAYONESA", "MOSTAZA", "PICANTE"],
        "Other": []
    }
    
    if "DAFLON" in desc_upper: return "Other"
    if "CROMOS" in desc_upper: return "Other"

    for category, tags in keywords.items():
        if category == "Other": continue
        for tag in tags:
            if tag in desc_upper:
                return category
    return "Other"

def extract_items(text):
    items = []
    pattern = r'^\s*(\d+)\s+(.+?)\s+(\d+\.\d+)\s+(\w+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s*$'
    for line in text.split('\n'):
        match = re.match(pattern, line)
        if match:
            item = InvoiceItem()
            item.number = match.group(1)
            item.description = match.group(2)
            item.quantity = float(match.group(3))
            item.unit_price = float(match.group(5))
            item.discount = float(match.group(6))
            item.line_price = float(match.group(7))
            item.itbms = float(match.group(8))
            item.item_price = float(match.group(9))
            item.category = categorize_item(item.description)
            items.append(item)
    return items

def check_model_availability(model_name):
    print(f"Checking for Ollama model: {model_name}...")
    try:
        import subprocess
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
        import subprocess
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

def generate_dashboard(invoices, aggregated_categories, ai_analysis):
    print("Generating Dashboard...")
    
    # Sort invoices by date for the trend chart
    invoices.sort(key=lambda x: x.date if x.date else datetime.min.date())
    
    # Prepare Category Chart data
    cat_labels = list(aggregated_categories.keys())
    cat_data = list(aggregated_categories.values())
    
    # Prepare Trend Chart data
    trend_labels = [str(inv.date) if inv.date else "Unknown" for inv in invoices]
    trend_data = [inv.total_amount for inv in invoices]
    
    # Simple HTML Template
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Invoice Expense Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body class="bg-gray-100 font-sans leading-normal tracking-normal">
        <div class="container mx-auto px-4 py-8">
            <h1 class="text-4xl font-bold text-gray-800 mb-8 text-center">Expense Analysis Dashboard</h1>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                <!-- Category Chart Section -->
                <div class="bg-white rounded-lg shadow-lg p-6">
                    <h2 class="text-2xl font-bold mb-4 text-gray-700">Spending by Category</h2>
                    <canvas id="expenseChart"></canvas>
                </div>
                
                <!-- AI Summary Section -->
                <div class="bg-white rounded-lg shadow-lg p-6 overflow-y-auto" style="max-height: 500px;">
                    <h2 class="text-2xl font-bold mb-4 text-gray-700">AI Executive Summary</h2>
                    <div class="prose max-w-none text-gray-600">
                        {ai_analysis.replace(chr(10), '<br>')} 
                    </div>
                </div>
            </div>
            
            <!-- Trend Chart Section -->
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-2xl font-bold mb-4 text-gray-700">Spending Trend (Total per Invoice)</h2>
                <div class="relative h-64 md:h-96">
                     <canvas id="trendChart"></canvas>
                </div>
            </div>
        </div>

        <script>
            // Category Pie Chart
            const ctx = document.getElementById('expenseChart').getContext('2d');
            new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    labels: {json.dumps(cat_labels)},
                    datasets: [{{
                        data: {json.dumps(cat_data)},
                        backgroundColor: [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', 
                            '#E7E9ED', '#76A346', '#FDB45C', '#949FB1', '#4D5360', '#B4F8C8', '#FFAEB9'
                        ]
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{ position: 'bottom' }}
                    }}
                }}
            }});
            
            // Trend Bar Chart
            const ctxTrend = document.getElementById('trendChart').getContext('2d');
            new Chart(ctxTrend, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(trend_labels)},
                    datasets: [{{
                        label: 'Invoice Total ($)',
                        data: {json.dumps(trend_data)},
                        backgroundColor: '#36A2EB',
                        borderColor: '#2482C2',
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'Amount ($)'
                            }}
                        }},
                        x: {{
                             title: {{
                                display: true,
                                text: 'Date'
                            }}
                        }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    with open("dashboard.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Dashboard saved to {os.path.abspath('dashboard.html')}")

# Main Execution
if __name__ == "__main__":
    if CONFIG.get("DownloadInvoice", False):
        download_gmail_attachments()

    if not check_model_availability(CONFIG["ollama_model"]):
        sys.exit(1)
        
    pdf_dir = CONFIG["pdf_directory"]
    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}")
        sys.exit(0)
        
    all_invoices = []
    aggregated_categories = {}
    total_spend_all = 0.0
    
    print(f"Found {len(pdf_files)} PDFs. Processing...")
    
    for pdf_file in pdf_files:
        print(f"Processing {pdf_file}...")
        try:
            with pdfplumber.open(pdf_file) as pdf:
                page = pdf.pages[0]
                text = page.extract_text()
                
                invoice = InvoiceData(os.path.basename(pdf_file))
                invoice.supermarket = detect_supermarket(text)
                invoice.date = detect_date(text)
                invoice.total_amount = detect_total(text)
                invoice.items = extract_items(text)
                
                all_invoices.append(invoice)
                total_spend_all += invoice.total_amount
                
                # Aggregate
                for item in invoice.items:
                    if item.category not in aggregated_categories:
                        aggregated_categories[item.category] = 0.0
                    aggregated_categories[item.category] += item.item_price
                    
        except Exception as e:
            print(f"Failed to process {pdf_file}: {e}")

    # Run Analysis
    ai_result = analyze_aggregated_data(aggregated_categories, total_spend_all)
    print(ai_result)
    
    # Generate Dashboard
    generate_dashboard(all_invoices, aggregated_categories, ai_result)
