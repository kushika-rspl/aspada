# # Copyright (c) 2025, kushika and contributors
# # For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, get_datetime, add_days, time_diff_in_hours
import calendar
from datetime import datetime
from collections import defaultdict


class OvertimeCalculation(Document):
	pass

# SHIFT_HOURS = 9  

def get_shift_hours(employee, date):
    shift_assignment = frappe.db.sql("""
        SELECT shift_type
        FROM `tabShift Assignment`
        WHERE employee = %s
        AND start_date <= %s
        AND (end_date >= %s OR end_date IS NULL)
        ORDER BY start_date DESC
        LIMIT 1
    """, (employee, date, date), as_dict=True)

    if not shift_assignment:
        frappe.throw(f"❌ No shift assignment found for Employee <b>{employee}</b> on <b>{date}</b>.")

    shift_type = shift_assignment[0].shift_type

    shift = frappe.db.get_value("Shift Type", shift_type, ["start_time", "end_time"], as_dict=True)

    if not shift or not shift.start_time or not shift.end_time:
        frappe.throw(
            f"❌ Shift Type <b>{shift_type}</b> for Employee <b>{employee}</b> on <b>{date}</b> is missing <code>start_time</code> or <code>end_time</code>."
        )

    # Convert times to datetime objects for calculation
    fmt = "%H:%M:%S"
    try:
        start_dt = datetime.strptime(str(shift.start_time), fmt)
        end_dt = datetime.strptime(str(shift.end_time), fmt)
    except Exception as e:
        frappe.throw(
            f"❌ Failed to parse start/end time for Shift Type <b>{shift_type}</b>: {e}"
        )

    # Handle overnight shifts (e.g. 22:00 to 06:00)
    if end_dt <= start_dt:
        end_dt = end_dt.replace(day=start_dt.day + 1)

    duration_hours = (end_dt - start_dt).total_seconds() / 3600
    duration_hours = round(duration_hours, 2)

    # Throw shift info to confirm what was picked
    # frappe.msgprint(
    #     f"✅ Shift selected for <b>{employee}</b> on <b>{date}</b>:<br>"
    #     f"Shift Type: <b>{shift_type}</b><br>"
    #     f"Start Time: <code>{shift.start_time}</code><br>"
    #     f"End Time: <code>{shift.end_time}</code><br>"
    #     f"Duration Calculated: <b>{duration_hours} hours</b>"
    # )


    return duration_hours




# def get_employee_overtime(employee, month, year):
#     total_ot = 0
#     ot_by_date = {}

#     last_day_of_month = calendar.monthrange(int(year), int(month))[1]

#     checkins = frappe.get_all(
#         "Employee Checkin",
#         filters={
#             "employee": employee,
#             "time": ["between", (f"{year}-{month}-01", f"{year}-{month}-{last_day_of_month}")]
#         },
#         fields=["time", "log_type", "custom_site_in", "custom_site_out", "custom_travelling_in", "custom_travelling_out"],
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
#         ot, daily_data = calculate_ot(in_time, out_time, month, year, is_travel=False, employee=employee)
#         total_ot += ot
#         for date, hrs in daily_data.items():
#             ot_by_date[date] = ot_by_date.get(date, 0) + hrs

#     for data in checkins:
#         if data.get("custom_site_in") and data.get("custom_site_out"):
#             ot, daily_data = calculate_ot(data["custom_site_in"], data["custom_site_out"], month, year, is_travel=False, employee=employee)
#             total_ot += ot
#             for date, hrs in daily_data.items():
#                 ot_by_date[date] = ot_by_date.get(date, 0) + hrs

#         if data.get("custom_travelling_in") and data.get("custom_travelling_out"):
#             ot, daily_data = calculate_ot(data["custom_travelling_in"], data["custom_travelling_out"], month, year, is_travel=True, employee=employee)
#             total_ot += ot
#             for date, hrs in daily_data.items():
#                 ot_by_date[date] = ot_by_date.get(date, 0) + hrs

#     return total_ot, ot_by_date


# def calculate_ot(start_time, end_time, selected_month, selected_year, is_travel=False, employee=None):
#     total_ot = 0
#     daily_ot_by_date = {}

#     start_time = get_datetime(start_time)
#     end_time = get_datetime(end_time)
#     current_date = getdate(start_time)

#     while current_date <= getdate(end_time):
#         weekday = current_date.weekday()  
#         next_day = add_days(current_date, 1)

#         if current_date.month != int(selected_month) or current_date.year != int(selected_year):
#             current_date = next_day
#             continue  

#         if (getdate(start_time).month != int(selected_month) or getdate(start_time).year != int(selected_year)) and current_date.day == 1:
#             day_start = get_datetime(f"{current_date} 00:00:00")
#         else:
#             day_start = max(start_time, get_datetime(f"{current_date} 00:00:00"))

#         if (getdate(end_time).month != int(selected_month) or getdate(end_time).year != int(selected_year)) and current_date == getdate(end_time):
#             day_end = get_datetime(f"{current_date} 23:59:59")
#         else:
#             day_end = min(end_time, get_datetime(f"{next_day} 00:00:00"))

#         time_spent = time_diff_in_hours(day_end, day_start)

#         if weekday == 6:  # Sunday
#             ot = time_spent if not is_travel else time_spent / 2
#         else:
#             shift_hours = get_shift_hours(employee, date=current_date)
#             ot = max(0, time_spent - shift_hours)

#             ot = ot if not is_travel else ot / 2

#         if ot > 0.5:
#             total_ot += ot

#         date_str = current_date.strftime("%Y-%m-%d")
#         daily_ot_by_date[date_str] = daily_ot_by_date.get(date_str, 0) + round(ot, 2)

#         current_date = next_day  # Move to next day

#     return total_ot, daily_ot_by_date



@frappe.whitelist()
def calculate_monthly_ot(employee, month, year):
    total_ot, breakdown_dict = get_employee_overtime(employee, month, year)

    from datetime import timedelta

    # Generate all dates in selected month
    days_in_month = calendar.monthrange(int(year), int(month))[1]
    all_dates = [f"{year}-{month.zfill(2)}-{str(day).zfill(2)}" for day in range(1, days_in_month + 1)]

    # Fill in OT values for all days (default to 0 if not in breakdown_dict)
    breakdown = []
    for date in all_dates:
        breakdown.append({
            "date": date,
            "ot_hours": round(breakdown_dict.get(date, 0), 2)
        })

    # Add total row
    breakdown.append({
        "date": date,
        "ot_hours": round(total_ot, 2)
    })

    return {
        "total_ot": round(total_ot, 2),
        "breakdown": breakdown
    }

def accumulate_time(start_time, end_time, time_buckets, category):
    start = get_datetime(start_time)
    end = get_datetime(end_time)
    current_date = getdate(start)

    while current_date <= getdate(end):
        next_day = add_days(current_date, 1)

        day_start = max(start, get_datetime(f"{current_date} 00:00:00"))
        day_end = min(end, get_datetime(f"{next_day} 00:00:00"))

        hours = time_diff_in_hours(day_end, day_start)

        time_buckets[str(current_date)][category] += hours

        current_date = next_day


def get_employee_overtime(employee, month, year):
    total_ot = 0
    ot_by_date = defaultdict(float)
    time_buckets = defaultdict(lambda: {"regular": 0, "site": 0, "travel": 0})

    last_day_of_month = calendar.monthrange(int(year), int(month))[1]

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
        accumulate_time(in_time, out_time, time_buckets, "regular")

    for data in checkins:
        if data.get("custom_site_in") and data.get("custom_site_out"):
            accumulate_time(data["custom_site_in"], data["custom_site_out"], time_buckets, "site")

        if data.get("custom_travelling_in") and data.get("custom_travelling_out"):
            accumulate_time(data["custom_travelling_in"], data["custom_travelling_out"], time_buckets, "travel")
    days_in_month = calendar.monthrange(int(year), int(month))[1]
    all_dates = [f"{year}-{month.zfill(2)}-{str(day).zfill(2)}" for day in range(1, days_in_month + 1)]

    for date in all_dates:
        date_obj = getdate(date)
        weekday = date_obj.weekday()

        # Get or default to zeroed buckets
        buckets = time_buckets.get(date, {"regular": 0, "site": 0, "travel": 0})

        total_time = buckets["regular"] + buckets["site"] + (buckets["travel"] / 2)

        # Print message
        frappe.msgprint(
            f"🗓️ <b>{date}</b><br>"
            f"• Regular: <b>{round(buckets['regular'], 2)} hrs</b><br>"
            f"• Site: <b>{round(buckets['site'], 2)} hrs</b><br>"
            f"• Travel: <b>{round(buckets['travel'], 2)} hrs</b><br>"
            f"• <b>Total considered for OT: {round(total_time, 2)} hrs</b>"
        )

    # for date, buckets in time_buckets.items():
    #     date_obj = getdate(date)
    #     weekday = date_obj.weekday()

    #     # Total time worked in the day
    #     total_time = buckets["regular"] + buckets["site"] + (buckets["travel"] / 2 if weekday != 6 else buckets["travel"])

    #     # Show accumulated hours
    #     frappe.msgprint(
    #         f"🗓️ <b>{date}</b><br>"
    #         f"• Regular: <b>{round(buckets['regular'], 2)} hrs</b><br>"
    #         f"• Site: <b>{round(buckets['site'], 2)} hrs</b><br>"
    #         f"• Travel: <b>{round(buckets['travel'], 2)} hrs</b><br>"
    #         f"• <b>Total considered for OT: {round(total_time, 2)} hrs</b>"
    #     )

        if weekday == 6:  # Sunday
            ot_hours = total_time
        else:
            shift_hours = get_shift_hours(employee, date)
            ot_hours = max(0, total_time - shift_hours)

        if ot_hours > 0.5:
            ot_by_date[date] += round(ot_hours, 2)
            total_ot += round(ot_hours, 2)

    return total_ot, ot_by_date
