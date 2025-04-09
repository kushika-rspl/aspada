# Copyright (c) 2025, kushika and contributors
# For license information, please see license.txt

# from frappe.model.document import Document
# import frappe
# from frappe.utils import getdate, get_datetime, add_days, time_diff_in_hours
# import calendar

# SHIFT_HOURS = 9  

# class OvertimeCalculation(Document):
#     pass

# def get_shift_hours(employee, current_date):
#     shift_type = frappe.db.get_value(
#         "Shift Assignment",
#         filters={
#             "employee": employee,
#             "start_date": ["<=", current_date],
#             "end_date": [">=", current_date],
#         },
#         fieldname="shift_type"
#     )

#     if shift_type:
#         return frappe.db.get_value("Shift Type", shift_type, "duration") or SHIFT_HOURS
#     return SHIFT_HOURS

# def mark_attendance(employee, current_date, log_note="Site/Travel Log"):
#     if frappe.db.exists("Attendance", {"employee": employee, "attendance_date": current_date}):
#         return  # Already marked

#     attendance = frappe.new_doc("Attendance")
#     attendance.employee = employee
#     attendance.attendance_date = current_date
#     attendance.status = "Present"
#     attendance.docstatus = 1
#     attendance.custom_log_reference = log_note  # Optional: you can remove or rename this if not using
#     attendance.insert(ignore_permissions=True)
#     frappe.db.commit()
#     frappe.msgprint(f"Attendance marked for {employee} on {current_date} due to {log_note}")

# def calculate_ot(start_time, end_time, selected_month, selected_year, is_travel=False, employee=None, mark_att=False):
#     total_ot = 0
#     start_time = get_datetime(start_time)
#     end_time = get_datetime(end_time)

#     current_date = getdate(start_time)

#     while current_date <= getdate(end_time):
#         weekday = current_date.weekday() 
#         next_day = add_days(current_date, 1)

#         if current_date.month != int(selected_month) or current_date.year != int(selected_year):
#             current_date = next_day
#             continue

#         shift_hours = get_shift_hours(employee, current_date)

#         day_start = max(start_time, get_datetime(f"{current_date} 00:00:00"))
#         day_end = min(end_time, get_datetime(f"{next_day} 00:00:00"))
#         time_spent = time_diff_in_hours(day_end, day_start)

#         if mark_att and employee:
#             mark_attendance(employee, current_date)

#         if weekday == 6:  
#             total_ot += time_spent if not is_travel else time_spent / 2
#         else:
#             ot_hours = max(0, time_spent - shift_hours)
#             total_ot += ot_hours if not is_travel else ot_hours / 2

#         current_date = next_day

#     return total_ot

# def get_employee_overtime(employee, month, year):
#     total_overtime = 0

#     last_day_of_month = calendar.monthrange(int(year), int(month))[1]

#     checkins = frappe.get_all(
#         "Employee Checkin",
#         filters={
#             "employee": employee,
#             "time": ["between", (f"{year}-{month}-01", f"{year}-{month}-{last_day_of_month}")]
#         },
#         fields=[
#             "time", "log_type", "custom_site_in", "custom_site_out",
#             "custom_travelling_in", "custom_travelling_out"
#         ],
#         order_by="time asc"
#     )

#     paired_logs = []
#     in_time = None

#     for log in checkins:
#         if log["log_type"] == "IN":
#             in_time = log["time"]
#         elif log["log_type"] == "OUT" and in_time:
#             paired_logs.append((in_time, log["time"]))
#             in_time = None

#     for in_time, out_time in paired_logs:
#         total_overtime += calculate_ot(in_time, out_time, month, year, is_travel=False, employee=employee)

#     for data in checkins:
#         if data.get("custom_site_in") and data.get("custom_site_out"):
#             total_overtime += calculate_ot(
#                 data["custom_site_in"],
#                 data["custom_site_out"],
#                 month, year,
#                 is_travel=False,
#                 employee=employee,
#                 mark_att=True
#             )

#         if data.get("custom_travelling_in") and data.get("custom_travelling_out"):
#             total_overtime += calculate_ot(
#                 data["custom_travelling_in"],
#                 data["custom_travelling_out"],
#                 month, year,
#                 is_travel=True,
#                 employee=employee,
#                 mark_att=True
#             )

#     return total_overtime

# @frappe.whitelist()
# def calculate_monthly_ot(employee, month, year):
#     return get_employee_overtime(employee, month, year)

# import frappe
from frappe.model.document import Document
import frappe
from frappe.utils import getdate, get_datetime, add_days, time_diff_in_hours
import calendar

class OvertimeCalculation(Document):
	pass

SHIFT_HOURS = 9  


def get_employee_overtime(employee, month, year):
    total_overtime = 0

    last_day_of_month = calendar.monthrange(int(year), int(month))[1]  # Returns (weekday, last_day)

    checkins = frappe.get_all(
        "Employee Checkin",
        filters={
            "employee": employee,
            "time": ["between", (f"{year}-{month}-01", f"{year}-{month}-{last_day_of_month}")]
        },
        fields=["time", "log_type", "custom_site_in", "custom_site_out", "custom_travelling_in", "custom_travelling_out"],
        order_by="time asc"
    )

    paired_logs = []
    in_time = None

    for log in checkins:
        if log["log_type"] == "IN":
            in_time = log["time"]
        elif log["log_type"] == "OUT" and in_time:
            paired_logs.append((in_time, log["time"]))
            in_time = None  

    for in_time, out_time in paired_logs:
        total_overtime += calculate_ot(in_time, out_time, month, year, is_travel=False)

    for data in checkins:
        if data.get("custom_site_in") and data.get("custom_site_out"):
            total_overtime += calculate_ot(data["custom_site_in"], data["custom_site_out"], month, year, is_travel=False)

        if data.get("custom_travelling_in") and data.get("custom_travelling_out"):
            total_overtime += calculate_ot(data["custom_travelling_in"], data["custom_travelling_out"], month, year, is_travel=True)

    return total_overtime

def calculate_ot(start_time, end_time, selected_month, selected_year, is_travel=False):
    total_ot = 0
    start_time = get_datetime(start_time)
    end_time = get_datetime(end_time)

    current_date = getdate(start_time)

    while current_date <= getdate(end_time):
        weekday = current_date.weekday()  
        next_day = add_days(current_date, 1)

        if current_date.month != int(selected_month) or current_date.year != int(selected_year):
            current_date = next_day
            continue  

        if (getdate(start_time).month != int(selected_month) or getdate(start_time).year != int(selected_year)) and current_date.day == 1:
            day_start = get_datetime(f"{current_date} 00:00:00")
        else:
            day_start = max(start_time, get_datetime(f"{current_date} 00:00:00"))

        if (getdate(end_time).month != int(selected_month) or getdate(end_time).year != int(selected_year)) and current_date == getdate(end_time):
            day_end = get_datetime(f"{current_date} 23:59:59")
        else:
            day_end = min(end_time, get_datetime(f"{next_day} 00:00:00"))

        time_spent = time_diff_in_hours(day_end, day_start)

        if weekday == 6:  
            total_ot += time_spent if not is_travel else time_spent / 2  # Full OT for normal/site work, Half for Travel
        else:  
            ot_hours = max(0, time_spent - SHIFT_HOURS)
            total_ot += ot_hours if not is_travel else ot_hours / 2  # Full OT for normal/site work, Half for Travel

        current_date = next_day  # Move to next day

    return total_ot

# def get_employee_overtime(employee, month, year):
#     total_overtime = 0

#     # Fetch all check-in/check-out logs for the employee
#     checkins = frappe.get_all(
#         "Employee Checkin",
#         filters={
#             "employee": employee,
#             "time": ["between", (f"{year}-{month}-01", f"{year}-{month}-31")]
#         },
#         fields=["time", "log_type", "custom_site_in", "custom_site_out", "custom_travelling_in", "custom_travelling_out"],
#         order_by="time asc"
#     )

#     paired_logs = []
#     in_time = None

#     # Pair IN/OUT logs
#     for log in checkins:
#         if log["log_type"] == "IN":
#             in_time = log["time"]
#         elif log["log_type"] == "OUT" and in_time:
#             paired_logs.append((in_time, log["time"]))
#             in_time = None  # Reset after pairing

#     # Calculate Normal Check-in/Check-out OT
#     for in_time, out_time in paired_logs:
#         total_overtime += calculate_ot(in_time, out_time, month, year, is_travel=False)

#     # Site OT Calculation
#     for data in checkins:
#         if data.get("custom_site_in") and data.get("custom_site_out"):
#             total_overtime += calculate_ot(data["custom_site_in"], data["custom_site_out"], month, year, is_travel=False)

#         # Travel OT Calculation (half OT)
#         if data.get("custom_travelling_in") and data.get("custom_travelling_out"):
#             total_overtime += calculate_ot(data["custom_travelling_in"], data["custom_travelling_out"], month, year, is_travel=True)

#     return total_overtime

@frappe.whitelist()
def calculate_monthly_ot(employee, month, year):
    return get_employee_overtime(employee, month, year)
