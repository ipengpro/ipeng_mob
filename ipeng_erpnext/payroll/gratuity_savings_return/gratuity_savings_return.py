import frappe
from frappe import _, bold
from frappe.utils import flt, get_datetime, get_link_to_form, add_days


def gratuity_savings_return_validate(doc, method=None):
    data = calculate_amount(doc.employee)
    doc.amount = data["amount"]
    doc.calculation_description = data["calculation_description"]
    if doc.docstatus == 1:
        doc.status = "Unpaid"

def calculate_amount(employee_name):
    data = {}
    data['amount'] = 0

    employee = frappe.get_doc("Employee", employee_name)

    if not employee.relieving_date:
        frappe.throw(
            _("Please set Relieving Date for employee: {0}").format(
                bold(get_link_to_form("Employee", employee_name))
            )
        )

    work_history = frappe.db.get_list(
        'Employee Work History',
        filters={
            'parent': employee_name,
        },
        fields=['from_date', 'current_salary', 'employment_type'],
        order_by='from_date asc'
    )

    if work_history:
        half_of_first_salary = work_history[0]['current_salary'] * 0.5
        salary_increase = max(0, work_history[-1]['current_salary'] - work_history[0]['current_salary'])
        sum_six_percent_amount = 0
        calculation_description = ''

        salary_change_history = list(filter(lambda x: x['current_salary'], work_history))
        end_of_probation_record = next((x for x in work_history \
            if (x['employment_type'] and 'probation' not in x['employment_type'].lower())))
        end_of_probation_date = end_of_probation_record['from_date'] if end_of_probation_record else None

        calculation_description += '''\
Half of First Salary: {half_of_first_salary}
Total Salary Increase: {salary_increase}
End of Probation Date: {end_of_probation_date}
-------------------------
'''.format(half_of_first_salary=half_of_first_salary, salary_increase=salary_increase, end_of_probation_date=end_of_probation_date)

        for i in range(0, len(salary_change_history)):
            current_salary = salary_change_history[i]['current_salary']
            start_date = salary_change_history[i]['from_date']
            end_date = add_days(salary_change_history[i+1]['from_date'], -1) if i+1 < len(salary_change_history) else employee.relieving_date

            if not end_of_probation_date or end_date <= end_of_probation_date:
                continue

            if start_date < end_of_probation_date:
                start_date = end_of_probation_date

            days_total = get_payment_days_total(employee_name, start_date, end_date)
            lwp_days = get_lwp_days_total(employee_name, start_date, end_date)
            days_total -= lwp_days

            if employee.employment_type != 'Part-time':
                six_percent_amount = days_total * (current_salary / 30) * 0.06
            else:
                six_percent_amount = days_total * current_salary * 0.06

            sum_six_percent_amount += six_percent_amount

            calculation_description += '''\
From Date: {start_date}
To Date: {end_date}
Working Days: {days_total}
Leave Without Pay: {lwp_days}
Salary: {current_salary}
Gratuity Savings: {six_percent_amount}
-------------------------
'''.format(start_date=start_date, end_date=end_date, days_total=days_total, lwp_days=lwp_days, 
    current_salary=current_salary, six_percent_amount=six_percent_amount)

        data['amount'] = sum_six_percent_amount + salary_increase + half_of_first_salary
        data['calculation_description'] = calculation_description

    else:
         frappe.throw(_('Employee has an empty work history'))

    return data   

def get_payment_days_total(employee_name, start_date, end_date):
    full_months = diff_month(end_date, start_date) - 1
    if full_months < 1:
        frappe.throw(_('Gratuity Savings Return cannot be calculated for less than a month'))

    days_total = 30 - start_date.day + 1
    days_total += 30 * full_months
    days_total += end_date.day

    return days_total

def get_lwp_days_total(employee_name, start_date, end_date):
    lwp_days_total = 0

    leaves_without_pay = frappe.db.sql('''
        SELECT l.from_date , l.to_date
        FROM `tabLeave Application` as l
        INNER JOIN `tabLeave Type` as lt on l.leave_type = lt.name
        WHERE lt.is_lwp = True
            AND l.docstatus = 1 
            AND l.status = 'Approved' 
            AND employee = %s
            AND l.from_date <= %s AND l.to_date >= %s
        ''', (employee_name, end_date, start_date), as_dict=True)

    for lwp in leaves_without_pay:
        from_date = max(start_date, lwp['from_date'])
        to_date = min(end_date, lwp['to_date'])
        lwp_days = (to_date - from_date).days + 1

        lwp_days_total += lwp_days
    
    return lwp_days_total
            

def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month