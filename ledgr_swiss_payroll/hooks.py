app_name = "ledgr_swiss_payroll"
app_title = "LEDGR Swiss Payroll"
app_publisher = "LEDGR"
app_description = "Swiss payroll automation app for Frappe v15 / ERPNext v15 / HRMS v15 — multi-mandate, AHV/AC + IS cantonal, certificat de salaire formulaire 11, pain.001 ISO 20022."
app_email = "kevinvarelamoreira@gmail.com"
app_license = "gpl-3.0"

required_apps = ["ledgr_core", "ledgr_chart_of_accounts_ch"]

# Apps
# ------------------

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "ledgr_swiss_payroll",
# 		"logo": "/assets/ledgr_swiss_payroll/logo.png",
# 		"title": "LEDGR Swiss Payroll",
# 		"route": "/ledgr_swiss_payroll",
# 		"has_permission": "ledgr_swiss_payroll.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/ledgr_swiss_payroll/css/ledgr_swiss_payroll.css"
# app_include_js = "/assets/ledgr_swiss_payroll/js/ledgr_swiss_payroll.js"

# include js, css files in header of web template
# web_include_css = "/assets/ledgr_swiss_payroll/css/ledgr_swiss_payroll.css"
# web_include_js = "/assets/ledgr_swiss_payroll/js/ledgr_swiss_payroll.js"

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Installation
# ------------

# before_install = "ledgr_swiss_payroll.install.before_install"
# after_install = "ledgr_swiss_payroll.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "ledgr_swiss_payroll.uninstall.before_uninstall"
# after_uninstall = "ledgr_swiss_payroll.uninstall.after_uninstall"

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"ledgr_swiss_payroll.tasks.all"
# 	],
# 	"daily": [
# 		"ledgr_swiss_payroll.tasks.daily"
# 	],
# 	"hourly": [
# 		"ledgr_swiss_payroll.tasks.hourly"
# 	],
# 	"weekly": [
# 		"ledgr_swiss_payroll.tasks.weekly"
# 	],
# 	"monthly": [
# 		"ledgr_swiss_payroll.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "ledgr_swiss_payroll.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "ledgr_swiss_payroll.event.get_events"
# }

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
