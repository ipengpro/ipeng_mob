import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
    get_datetime,
    getdate,
)
from erpnext.hr.doctype.employee_work_history.employee_work_history import EmployeeWorkHistory
from erpnext.hr.doctype.employee_promotion.employee_promotion import EmployeePromotion
from erpnext.hr.doctype.employee_transfer.employee_transfer import EmployeeTransfer


def update_work_history_on_promotion(doc, method=None):
        employee = frappe.get_doc("Employee", doc.employee)
        employee = update_employee_work_history(
            employee=employee, details=doc.promotion_details, date=doc.promotion_date
        )
        employee.save()

def delete_work_history_on_promotion(doc, method=None):
        employee = frappe.get_doc("Employee", doc.employee)
        delete_employee_work_history(
            employee=employee, details=doc.promotion_details, date=doc.promotion_date
        )


def update_employee_work_history(employee, details, date=None):
    if not employee.work_history:
        employee.append(
            "work_history",
            {
                "branch": employee.branch,
                "designation": employee.designation,
                "department": employee.department,
                "from_date": employee.date_of_joining,
                "designation_category": employee.designation_category,
                "employment_type": employee.employment_type,
                "grade": employee.grade,
                "rate": employee.rate,
                "level": employee.level,
                "salary": employee.current_salary,
            },
        )

    work_history = {}
    for item in details:
        field = frappe.get_meta("Employee").get_field(item.fieldname)
        if not field:
            continue
        fieldtype = field.fieldtype
        new_data = item.new
        if fieldtype == "Currency" and new_data:
            new_data = float(new_data)
        if item.fieldname in ["department", "designation", "branch", "designation_category", "employment_type", "grade", "rate", "level", "current_salary"]:
            work_history[item.fieldname] = new_data

    if work_history:
        work_history["from_date"] = date
        employee.append("work_history", work_history)

    return employee


def delete_employee_work_history(details, employee, date):
    filters = {}
    for d in details:
        for history in employee.work_history:
            if d.property == "Department" and history.department == d.new:
                department = d.new
                filters["department"] = department
            if d.property == "Designation" and history.designation == d.new:
                designation = d.new
                filters["designation"] = designation
            if d.property == "Branch" and history.branch == d.new:
                branch = d.new
                filters["branch"] = branch
            if date and date == history.from_date:
                filters["from_date"] = date
            if d.property == "Designation Category" and history.designation_category == d.new:
                filters["designation_category"] = d.new
            if d.property == "Employment Type" and history.employment_type == d.new:
                filters["employment_type"] = d.new
            if d.property == "Grade" and history.grade == d.new:
                filters["grade"] = d.new
            if d.property == "Rate" and history.rate == d.new:
                filters["rate"] = d.new
            if d.property == "Level" and history.level == d.new:
                filters["level"] = d.new
            if d.property == "Current Salary" and history.current_salary == d.new:
                filters["current_salary"] = d.new
    if filters:
        frappe.db.delete("Employee Work History", filters)

