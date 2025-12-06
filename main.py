import sys
import glob
import os
import webbrowser
import pdfplumber

from config import CONFIG
from models import InvoiceData
from gmail_service import download_gmail_attachments
from ai_analyzer import check_model_availability, analyze_aggregated_data
from invoice_parser import detect_supermarket, detect_date, detect_total, extract_items
from dashboard_generator import generate_dashboard

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
    
    # Auto-open Dashboard
    dashboard_path = os.path.abspath("dashboard.html")
    print(f"Opening dashboard: {dashboard_path}")
    webbrowser.open(f"file://{dashboard_path}")
