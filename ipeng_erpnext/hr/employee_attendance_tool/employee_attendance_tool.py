import json
from unicodedata import name

import frappe
from frappe.utils import getdate
from erpnext.hr.doctype.leave_application.leave_application import get_leave_balance_on

@frappe.whitelist()
def mark_employee_attendance(employee_list, status, date, leave_type=None, company=None):

    leave_approver_name = frappe.db.get_value("User", frappe.session.user, "full_name", cache=True)
    employee_list = json.loads(employee_list)
    for employee in employee_list:

        if status == "On Leave" and leave_type:
            leave_type = leave_type
        else:
            leave_type = None

        company = frappe.db.get_value("Employee", employee["employee"], "Company", cache=True)

        if "Security Guard Manager" in frappe.get_roles(frappe.user) and status == "On Leave":
            
            if get_leave_balance_on(employee=employee.get("employee"), 
            leave_type=leave_type, date=getdate(date), to_date=getdate(date),
            consider_all_leaves_in_the_allocation_period=True) > 0 or leave_type == "Leave Without Pay":
                leave_application = frappe.get_doc(
                    dict(
                        doctype="Leave Application",
                        employee=employee.get("employee"),
                        from_date=getdate(date),
                        to_date=getdate(date),
                        leave_type=leave_type,
                        company=company,
                        status="Approved",
                        leave_approver=frappe.session.user,
                        leave_approver_name=leave_approver_name
                    )
                )
                leave_application.insert()
                leave_application.submit()
            else:
                frappe.msgprint(msg=f"%s does not have enough leaves" % employee.get("employee_name"), title="Insufficient Balance")

        else:
            attendance = frappe.get_doc(
                dict(
                    doctype="Attendance",
                    employee=employee.get("employee"),
                    employee_name=employee.get("employee_name"),
                    attendance_date=getdate(date),
                    status=status,
                    leave_type=leave_type,
                    company=company,
            )
            )
            attendance.insert()
            attendance.submit()