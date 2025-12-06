import pdfplumber
from invoice_parser import detect_supermarket, extract_items, detect_date, detect_total
import os

def verify_parser(pdf_path="sample_invoice.pdf"):
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found.")
        return

    print(f"Verifying {pdf_path}...")
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages)
        
    print("--- Extracted Text Start ---")
    print(text)
    print("--- Extracted Text End ---")

    supermarket = detect_supermarket(text)
    print(f"Detected Supermarket: {supermarket}")
    
    date = detect_date(text)
    print(f"Detected Date: {date}")
    
    total = detect_total(text)
    print(f"Detected Total: {total}")

    items = extract_items(text)
    print(f"Extracted {len(items)} items:")
    for item in items:
        print(f"  - {item.description} (Qty: {item.quantity}, Price: {item.item_price})")

if __name__ == "__main__":
    verify_parser()
