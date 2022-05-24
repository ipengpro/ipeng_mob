import frappe


@frappe.whitelist()
def get_employee_fields_label():
    fields = []
    for df in frappe.get_meta("Employee").get("fields"):
        if df.fieldname in [
            "salutation",
            "user_id",
            "employee_number",
            "employment_type",
            "holiday_list",
            "branch",
            "department",
            "designation",
            "grade",
            "rate",
            "level",
            "notice_number_of_days",
            "reports_to",
            "leave_policy",
            "company_email",
        ]:
            fields.append({"value": df.fieldname, "label": df.label})
    return fields
