from . import __version__ as app_version

app_name = "ipeng_erpnext"
app_title = "IPengineering - ERPnext"
app_publisher = "IPengineering"
app_description = "Customized ERPnext"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "hassan.salah@ipengpro.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/ipeng_erpnext/css/ipeng_erpnext.css"
# app_include_js = "/assets/ipeng_erpnext/js/ipeng_erpnext.js"

# include js, css files in header of web template
# web_include_css = "/assets/ipeng_erpnext/css/ipeng_erpnext.css"
# web_include_js = "/assets/ipeng_erpnext/js/ipeng_erpnext.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "ipeng_erpnext/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Employee Attendance Tool": "public/js/employee_attendance_tool.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "ipeng_erpnext.install.before_install"
# after_install = "ipeng_erpnext.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "ipeng_erpnext.uninstall.before_uninstall"
# after_uninstall = "ipeng_erpnext.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "ipeng_erpnext.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Salary Slip": "ipeng_erpnext.payroll.salary_slip.salary_slip.CustomSalarySlip",
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
	"Employee Promotion": {
		"on_submit": "ipeng_erpnext.hr.employee_work_history.employee_work_history.update_work_history_on_promotion",
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"ipeng_erpnext.tasks.all"
# 	],
# 	"daily": [
# 		"ipeng_erpnext.tasks.daily"
# 	],
# 	"hourly": [
# 		"ipeng_erpnext.tasks.hourly"
# 	],
# 	"weekly": [
# 		"ipeng_erpnext.tasks.weekly"
# 	]
# 	"monthly": [
# 		"ipeng_erpnext.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "ipeng_erpnext.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"erpnext.hr.utils.get_employee_fields_label": "ipeng_erpnext.utils.get_employee_fields_label",
	"erpnext.hr.doctype.employee_attendance_tool.employee_attendance_tool.mark_employee_attendance": "ipeng_erpnext.hr.employee_attendance_tool.employee_attendance_tool.mark_employee_attendance"
}

#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "ipeng_erpnext.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"ipeng_erpnext.auth.validate"
# ]

# Translation
# --------------------------------

# Make link fields search translated document names for these DocTypes
# Recommended only for DocTypes which have limited documents with untranslated names
# For example: Role, Gender, etc.
# translated_search_doctypes = []
