// Copyright (c) 2025, kushika and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Overtime Calculation", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Overtime Calculation', {
    employee: function(frm) {
        calculate_ot(frm);
    },
    month: function(frm) {
        calculate_ot(frm);
    },
    year: function(frm) {
        calculate_ot(frm);
    }
});

function calculate_ot(frm) {
    if (frm.doc.employee && frm.doc.month && frm.doc.year) {
        frappe.call({
            method: "aspadha_cutomization.aspadha_cutomization.doctype.overtime_calculation.overtime_calculation.calculate_monthly_ot",
            args: {
                employee: frm.doc.employee,
                month: frm.doc.month,
                year: frm.doc.year
            },
            callback: function(response) {
                if (response.message) {
                    frm.set_value("total_ot_hours", response.message);
                    frm.refresh_field("total_ot_hours");
                }
            }
        });
    }
}
