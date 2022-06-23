from datetime import datetime

import frappe
from frappe import _
from frappe.utils import (
    add_days,
    cint,
    date_diff,
    flt,
    cstr,
    getdate,
)

from erpnext.payroll.doctype.salary_slip.salary_slip import SalarySlip
from frappe.utils.data import add_to_date

class CustomSalarySlip(SalarySlip):

    def get_working_days_details(
            self, joining_date=None, relieving_date=None, lwp=None, for_preview=0
        ):
            
            payroll_based_on = frappe.db.get_value("Payroll Settings", None, "payroll_based_on")
            include_holidays_in_total_working_days = frappe.db.get_single_value(
                "Payroll Settings", "include_holidays_in_total_working_days"
            )

            working_days = date_diff(self.end_date, self.start_date) + 1
            if for_preview:
                self.total_working_days = working_days
                self.payment_days = working_days
                return

            holidays = self.get_holidays_for_employee(self.start_date, self.end_date)

            if not payroll_based_on:
                frappe.throw(_("Please set Payroll based on in Payroll settings"))

            if payroll_based_on == "Attendance":
                actual_lwp, absent = self.calculate_lwp_ppl_and_absent_days_based_on_attendance(holidays)
                self.absent_days = absent
            else:
                actual_lwp = self.calculate_lwp_or_ppl_based_on_leave_application(holidays, working_days)

            # fixed a bug where after holidays count is subtracted, the leave without pay are not well calculated anymore
            if not cint(include_holidays_in_total_working_days):
                working_days -= len(holidays)
                if working_days < 0:
                    frappe.throw(_("There are more holidays than working days this month."))

            if not lwp:
                lwp = actual_lwp
            elif lwp != actual_lwp:
                frappe.msgprint(
                    _("Leave Without Pay does not match with approved {} records").format(payroll_based_on)
                )

            self.leave_without_pay = lwp
            self.total_working_days = working_days
            
            working_days_adjustment = 0

            # Change working days to 30
            start_date = getdate(self.start_date)
            end_date = getdate(self.end_date)
            start_date_full_time = None
            end_date_full_time = None

            if start_date.day == 1 \
                and start_date.month == end_date.month \
                and start_date.year == end_date.year \
                and add_to_date(start_date, months=1, days=-1) == end_date:

                working_days_adjustment = 30 - working_days
                self.total_working_days = 30

                start_date_full_time = frappe.utils.add_months(start_date, 1)
                end_date_full_time = frappe.utils.add_to_date(start_date, months=2, days=-1)

            # get total present days
            total_present_days = self.get_present_days(start_date, end_date)

            try:
                self.present_days = total_present_days
                self.start_date_full_time = start_date_full_time
                self.end_date_full_time = end_date_full_time
            except AttributeError:
                frappe.msgprint("present_days, start_date_full_time and end_date_full_time attribute missing in Salary Slip")

            # Get promotion days and salary difference
            promotion_working_days = None
            salary_difference = None
            promotion_present_days = None

            employee = frappe.get_doc("Employee", self.employee)
            if employee.employment_type == "Full-time" and self.start_date_full_time and self.end_date_full_time:
                start_date = self.start_date_full_time
                end_date = self.end_date_full_time

            promotion = self.get_promotion(start_date, end_date)

            if promotion:
                if employee.employment_type != "Full-time" or self.start_date_full_time: # eliminate case for full timers for dates less than a month
                    salary_difference = self.get_salary_difference(promotion)
                    
                    promotion_working_days = date_diff(end_date, promotion.promotion_date) + 1
                    lwp_during_promotion = self.calculate_lwp_or_ppl_based_on_leave_application_custom_start(holidays, promotion_working_days, promotion.promotion_date)
                    promotion_working_days = working_days - date_diff(promotion.promotion_date, start_date)
                    promotion_working_days -= lwp_during_promotion

                    promotion_present_days = self.get_present_days(promotion.promotion_date, end_date)

            try:
                self.promotion_working_days = promotion_working_days
                self.promotion_salary_difference = salary_difference
                self.promotion_present_days = promotion_present_days
            except AttributeError:
                frappe.msgprint("promotion_working_days, promotion_salary_difference and promotion_present_days attribute missing in Salary Slip")


            payment_days = self.get_payment_days(
                joining_date, relieving_date, include_holidays_in_total_working_days
            )
            payment_days += working_days_adjustment

            if flt(payment_days) > flt(lwp):
                self.payment_days = flt(payment_days) - flt(lwp)

                if payroll_based_on == "Attendance":
                    self.payment_days -= flt(absent)

                consider_unmarked_attendance_as = (
                    frappe.db.get_value("Payroll Settings", None, "consider_unmarked_attendance_as") or "Present"
                )

                if payroll_based_on == "Attendance" and consider_unmarked_attendance_as == "Absent":
                    unmarked_days = self.get_unmarked_days(include_holidays_in_total_working_days)
                    self.absent_days += unmarked_days  # will be treated as absent
                    self.payment_days -= unmarked_days
            else:
                self.payment_days = 0


    def calculate_lwp_or_ppl_based_on_leave_application_custom_start(self,  holidays, working_days, start_date):
        lwp = 0
        holidays = "','".join(holidays)
        daily_wages_fraction_for_half_day = (
            flt(frappe.db.get_value("Payroll Settings", None, "daily_wages_fraction_for_half_day")) or 0.5
        )

        for d in range(working_days):
            date = add_days(cstr(getdate(start_date)), d)
            leave = get_lwp_or_ppl_for_date(date, self.employee, holidays)

            if leave:
                equivalent_lwp_count = 0
                is_half_day_leave = cint(leave[0].is_half_day)
                is_partially_paid_leave = cint(leave[0].is_ppl)
                fraction_of_daily_salary_per_leave = flt(leave[0].fraction_of_daily_salary_per_leave)

                equivalent_lwp_count = (1 - daily_wages_fraction_for_half_day) if is_half_day_leave else 1

                if is_partially_paid_leave:
                    equivalent_lwp_count *= (
                        fraction_of_daily_salary_per_leave if fraction_of_daily_salary_per_leave else 1
                    )

                lwp += equivalent_lwp_count

        return lwp

    def get_promotion(self, start_date, end_date):
        
        promotion_names = frappe.db.get_list(
            "Employee Promotion",
            filters={
                "employee": self.employee,
                "promotion_date": ["between", [start_date, end_date]],
                "docstatus": ["!=", 2]
            },
            pluck='name'
        )

        if promotion_names:
            return frappe.get_doc("Employee Promotion", promotion_names[0])

    def get_salary_difference(self, promotion):
        if not promotion:
            return

        promotion_details = []
        promotion_details = frappe.db.get_all(
            'Employee Property History', 
            filters={'parent': promotion.name},
            fields={'property', 'fieldname', 'current', 'new'}
        )
        
        employee = frappe.get_doc('Employee', self.employee)
        old_ranking = [employee.grade, employee.rate, employee.level, employee.designation_category]
        new_ranking = [employee.grade, employee.rate, employee.level, employee.designation_category]

        for detail in promotion_details:
            if detail['fieldname'] == 'grade':
                new_ranking[0] = detail['new']
            elif detail['fieldname'] == 'rate':
                new_ranking[1] = detail['new']
            elif detail['fieldname'] == 'level':
                new_ranking[2] = detail['new']
            elif detail['fieldname'] == 'designation_category':
                new_ranking[3] = detail['new']
                
        old_salary = frappe.db.get_list('Salary Grade',
                        filters={'grade': old_ranking[0], 'rate': old_ranking[1], 'level': old_ranking[2], 'designation_category': old_ranking[3]},
                        pluck='amount',
                        order_by='date desc')
                        
        new_salary = frappe.db.get_list('Salary Grade',
                        filters={'grade': new_ranking[0], 'rate': new_ranking[1], 'level': new_ranking[2], 'designation_category': new_ranking[3]},
                        pluck='amount',
                        order_by='date desc')
        
        if old_salary and new_salary:
            old_salary = old_salary[0]
            new_salary = new_salary[0]

            if new_salary != old_salary:
                return new_salary - old_salary

    def get_present_days(self, start_date, end_date):
        return frappe.get_all(
            "Attendance",
            filters={
                "status": "Present",
                "attendance_date": ["between", [start_date, end_date]],
                "employee": self.employee,
                "docstatus": 1,
            },
            fields=["COUNT(*) as present_days"],
        )[0].present_days


def get_lwp_or_ppl_for_date(date, employee, holidays):
	LeaveApplication = frappe.qb.DocType("Leave Application")
	LeaveType = frappe.qb.DocType("Leave Type")

	is_half_day = (
		frappe.qb.terms.Case()
		.when(
			(
				(LeaveApplication.half_day_date == date)
				| (LeaveApplication.from_date == LeaveApplication.to_date)
			),
			LeaveApplication.half_day,
		)
		.else_(0)
	).as_("is_half_day")

	query = (
		frappe.qb.from_(LeaveApplication)
		.inner_join(LeaveType)
		.on((LeaveType.name == LeaveApplication.leave_type))
		.select(
			LeaveApplication.name,
			LeaveType.is_ppl,
			LeaveType.fraction_of_daily_salary_per_leave,
			(is_half_day),
		)
		.where(
			(((LeaveType.is_lwp == 1) | (LeaveType.is_ppl == 1)))
			& (LeaveApplication.docstatus == 1)
			& (LeaveApplication.status == "Approved")
			& (LeaveApplication.employee == employee)
			& ((LeaveApplication.salary_slip.isnull()) | (LeaveApplication.salary_slip == ""))
			& ((LeaveApplication.from_date <= date) & (date <= LeaveApplication.to_date))
		)
	)

	# if it's a holiday only include if leave type has "include holiday" enabled
	if date in holidays:
		query = query.where((LeaveType.include_holiday == "1"))

	return query.run(as_dict=True)
