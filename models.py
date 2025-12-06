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
