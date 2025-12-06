from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import random
from datetime import datetime, timedelta
import os

def random_date(start_date, end_date):
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

def generate_invoice(filename, supermarket_name, invoice_date):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Header
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 50, f"Emisor: {supermarket_name}")
    c.drawString(50, height - 70, f"Fecha: {invoice_date.strftime('%d/%m/%Y')}")
    c.drawString(50, height - 90, f"Factura #: {random.randint(10000, 99999)}")

    # Column Headers (simulation)
    y = height - 130
    c.setFont("Helvetica", 10)
    
    items_data = [
        ("LECHE ENTERA", "UNID", 1.50),
        ("PAN MOLDE", "UNID", 2.00),
        ("ARROZ ESPECIAL", "KG", 3.25),
        ("JABON DE BAÑO", "UNID", 0.95),
        ("POLLO ENTERO", "KG", 5.50),
        ("CEREAL DE MAIZ", "UNID", 4.10),
        ("MANZANA ROJA", "KG", 2.30),
        ("TUNA EN AGUA", "LATA", 1.85),
        ("ACEITE VEGETAL", "LITRO", 2.99),
        ("SALCHICHA DE POLLO", "PAQ", 1.25)
    ]

    total = 0.0
    items_count = random.randint(3, 8)

    c.drawString(50, y, "Items Details:")
    y -= 20

    for i in range(1, items_count + 1):
        desc, unit, price = random.choice(items_data)
        qty = round(random.uniform(1.0, 5.0), 3)
        discount = 0.00
        line_price = round(qty * price, 3) 
        itbms = round(line_price * 0.07, 3) 
        item_price = round(line_price + itbms, 3)

        total += item_price

        # Groups: 1=Num, 2=Desc, 3=Qty, 4=Unit, 5=UnitPrice, 6=Disc, 7=LinePrice, 8=ITBMS, 9=ItemPrice
        line_text = f"{i}   {desc}   {qty:.3f}   {unit}   {price:.3f}   {discount:.3f}   {line_price:.3f}   {itbms:.3f}   {item_price:.3f}"
        
        c.drawString(50, y, line_text)
        y -= 15

    # Footer
    y -= 20
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, f"Total {total:.2f}")

    c.save()
    print(f"Generated {filename}")

if __name__ == "__main__":
    output_dir = "samplepdf"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    start_date = datetime(2025, 10, 1)
    end_date = datetime(2025, 11, 30)

    supermarkets = ["La Gran Despensa", "Super Alfa"]
    
    for supermarket in supermarkets:
        for i in range(5):
            date = random_date(start_date, end_date)
            # Create a safe filename
            safe_name = supermarket.replace(" ", "_")
            filename = os.path.join(output_dir, f"Invoice_{safe_name}_{date.strftime('%Y%m%d')}_{i+1}.pdf")
            generate_invoice(filename, supermarket, date)
