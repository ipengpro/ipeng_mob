from math import floor

import frappe
from frappe import _, bold
from frappe.utils import getdate

from erpnext.payroll.doctype.gratuity.gratuity import (
    Gratuity, calculate_amount_based_on_current_slab, calculate_work_experience,
    get_applicable_components, get_gratuity_rule_slabs, get_last_salary_slip)


class CustomGratuity(Gratuity):
    def validate(self):
        data = calculate_work_experience_and_amount(self.employee, self.gratuity_rule)
        self.current_work_experience = data["current_work_experience"]
        self.amount = data["amount"]
        self.base_amount = data["total_applicable_components_amount"] # modified
        if self.docstatus == 1:
            self.status = "Unpaid"


@frappe.whitelist()
def calculate_work_experience_and_amount(employee, gratuity_rule):
    current_work_experience = calculate_work_experience(employee, gratuity_rule) or 0
    gratuity_amount = calculate_gratuity_amount(employee, gratuity_rule, current_work_experience) or 0

    ### modified
    applicable_earnings_component = get_applicable_components(gratuity_rule)
    total_applicable_components_amount = get_total_applicable_component_amount(
        employee, applicable_earnings_component, gratuity_rule
    )
    ###

    return {
        "current_work_experience": current_work_experience, 
        "amount": gratuity_amount, 
        "total_applicable_components_amount": total_applicable_components_amount # modified
    }

def calculate_gratuity_amount(employee, gratuity_rule, experience):
    applicable_earnings_component = get_applicable_components(gratuity_rule)
    total_applicable_components_amount = get_total_applicable_component_amount(
        employee, applicable_earnings_component, gratuity_rule
    )

    calculate_gratuity_amount_based_on = frappe.db.get_value(
        "Gratuity Rule", gratuity_rule, "calculate_gratuity_amount_based_on"
    )
    gratuity_amount = 0
    slabs = get_gratuity_rule_slabs(gratuity_rule)
    slab_found = False
    year_left = experience

    for slab in slabs:
        if calculate_gratuity_amount_based_on == "Current Slab":
            slab_found, gratuity_amount = calculate_amount_based_on_current_slab(
                slab.from_year,
                slab.to_year,
                experience,
                total_applicable_components_amount,
                slab.fraction_of_applicable_earnings,
            )
            if slab_found:
                break

        elif calculate_gratuity_amount_based_on == "Sum of all previous slabs":
            if slab.to_year == 0 and slab.from_year == 0:
                gratuity_amount += (
                    year_left * total_applicable_components_amount * slab.fraction_of_applicable_earnings
                )
                slab_found = True
                break

            if experience > slab.to_year and experience > slab.from_year and slab.to_year != 0:
                gratuity_amount += (
                    (slab.to_year - slab.from_year)
                    * total_applicable_components_amount
                    * slab.fraction_of_applicable_earnings
                )
                year_left -= slab.to_year - slab.from_year
                slab_found = True
            elif slab.from_year <= experience and (experience < slab.to_year or slab.to_year == 0):
                gratuity_amount += (
                    year_left * total_applicable_components_amount * slab.fraction_of_applicable_earnings
                )
                slab_found = True

    if not slab_found:
        frappe.throw(
            _("No Suitable Slab found for Calculation of gratuity amount in Gratuity Rule: {0}").format(
                bold(gratuity_rule)
            )
        )
    return gratuity_amount

def get_total_applicable_component_amount(employee, applicable_earnings_component, gratuity_rule):
    sal_slip = get_last_salary_slip(employee)
    if not sal_slip:
        frappe.throw(_("No Salary Slip is found for Employee: {0}").format(bold(employee)))
    component_and_amounts = frappe.get_all(
        "Salary Detail",
        filters={
            "docstatus": 1,
            "parent": sal_slip,
            "parentfield": "earnings",
            "salary_component": ("in", applicable_earnings_component),
        },
        fields=["amount"],
    )
    total_applicable_components_amount = 0
    if not len(component_and_amounts):
        frappe.throw(_("No Applicable Component is present in last month salary slip"))
    for data in component_and_amounts:
        total_applicable_components_amount += data.amount

    ### modified
    salary_increase_from_level = get_amount_due_from_next_level_promotion(employee)
    total_applicable_components_amount += salary_increase_from_level
    ###

    return total_applicable_components_amount

def get_amount_due_from_next_level_promotion(employee_name):
    try:
        employee = frappe.get_doc("Employee", employee_name)
        if employee.employment_type != 'Full-time':
            return 0

        if employee.next_level_promotion:
            salary_promotion_detail = frappe.db.get_list(
                'Employee Property History',
                filters={
                    'parent': employee.next_level_promotion,
                    'fieldname': 'current_salary'
                },
                fields=['current', 'new']
            )

            if salary_promotion_detail:
                salary_promotion_detail = salary_promotion_detail[0]
                salary_difference = float(salary_promotion_detail['new']) - float(salary_promotion_detail['current'])
                months_since_last_promotion = diff_month(getdate(employee.relieving_date), getdate(employee.last_promotion_date))
                
                if months_since_last_promotion > 0 and salary_difference > 0:
                    amount_due_from_next_promotion = salary_difference * (months_since_last_promotion / 24)
                    return amount_due_from_next_promotion

    except Exception as e:
        frappe.throw(str(e))

    return 0

def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month