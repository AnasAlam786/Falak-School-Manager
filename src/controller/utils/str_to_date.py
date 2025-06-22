from datetime import datetime, date

def str_to_date(value):
    if isinstance(value, (date, datetime)):
        return value.strftime('%d/%m/%Y')
    formats = ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y")
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError("Invalid date format! Please enter a valid date.")
