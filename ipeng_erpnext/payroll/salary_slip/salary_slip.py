from datetime import datetime

import frappe
from frappe import _
from frappe.utils import (
	cint,
	date_diff,
	flt,
)

from erpnext.payroll.doctype.salary_slip.salary_slip import SalarySlip

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

			if not cint(include_holidays_in_total_working_days):
				working_days -= len(holidays)
				if working_days < 0:
					frappe.throw(_("There are more holidays than working days this month."))

			if not payroll_based_on:
				frappe.throw(_("Please set Payroll based on in Payroll settings"))

			if payroll_based_on == "Attendance":
				actual_lwp, absent = self.calculate_lwp_ppl_and_absent_days_based_on_attendance(holidays)
				self.absent_days = absent
			else:
				actual_lwp = self.calculate_lwp_or_ppl_based_on_leave_application(holidays, working_days)

			if not lwp:
				lwp = actual_lwp
			elif lwp != actual_lwp:
				frappe.msgprint(
					_("Leave Without Pay does not match with approved {} records").format(payroll_based_on)
				)

			self.leave_without_pay = lwp
			self.total_working_days = working_days
			
			working_days_adjustment = 0

			if self.start_date and self.end_date:
				start_date = datetime.strptime(self.start_date, '%Y-%m-%d') if isinstance(self.start_date, str) else self.start_date
				end_date = datetime.strptime(self.end_date, '%Y-%m-%d') if isinstance(self.end_date, str) else self.end_date
				if start_date.day == 1 \
					and start_date.month == end_date.month \
					and start_date.year == end_date.year \
					and (end_date.day >= 30 or (end_date.month == 2 and end_date.day >= 28)):
					working_days_adjustment = 30 - working_days
					self.total_working_days = 30

			total_present_days = frappe.get_all(
			"Attendance",
			filters={
				"status": "Present",
				"attendance_date": ["between", [start_date, end_date]],
				"employee": self.employee,
				"docstatus": 1,
			},
			fields=["COUNT(*) as present_days"],
		)[0].present_days


			try:
				self.present_days = total_present_days
			except AttributeError:
				print("present_days attribute missing in Salary Slip")


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
