from datetime import datetime, date

def str_to_date(value):
    if isinstance(value, (date, datetime)):
        return value.strftime('%d/%m/%Y')
    formats = ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y")
    for fmt in formats:
        try:
            parsed_date = datetime.strptime(value, fmt)
            return parsed_date.strftime('%d-%m-%Y')
        except ValueError:
            continue
    raise ValueError(f"'{value}' is an invalid date format! Please enter a valid date.")
