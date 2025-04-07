import frappe
from frappe.model.document import Document
from datetime import datetime
import calendar

def set_custom_days_in_month(doc, method):
    """Automatically set number of days in month based on start_date"""
    print("Inside function")
    if doc.start_date:
        start_date = datetime.strptime(doc.start_date, "%Y-%m-%d")
        year = start_date.year
        month = start_date.month

        # Get the number of days in the selected month
        days_in_month = calendar.monthrange(year, month)[1]

        # Set the value in custom_days_in_month field
        doc.custom_days_in_month = days_in_month
