import re
from datetime import datetime
from models import InvoiceItem
from ai_analyzer import categorize_item_with_ai

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
                
    # Fallback to AI
    return categorize_item_with_ai(description)

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
