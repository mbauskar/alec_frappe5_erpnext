from __future__ import unicode_literals
from frappe import _

app_name = "erpnext"
app_title = "ERPNext"
app_publisher = "Frappe Technologies Pvt. Ltd. and Contributors"
app_description = "Open Source Enterprise Resource Planning for Small and Midsized Organizations"
app_icon = "icon-th"
app_color = "#e74c3c"
app_version = "6.4.4"
github_link = "https://github.com/frappe/erpnext"

error_report_email = "support@erpnext.com"

app_include_js = ["assets/js/erpnext.min.js","assets/js/plugins/slick.checkboxselectcolumn.js","assets/js/plugins/slick.cellcopymanager.js","assets/js/plugins/slick.cellrangeselector.js","assets/js/plugins/slick.cellrangedecorator.js","assets/js/plugins/slick.autotooltips.js","assets/js/plugins/slick.rowselectionmodel.js","assets/js/plugins/slick.cellselectionmodel.js","assets/js/plugins/slick.columnpicker.js"]
app_include_css = ["assets/css/erpnext.css","assets/css/jquery.dataTables.css","assets/css/dataTables.bootstrap.css"]
web_include_js = "assets/js/erpnext-web.min.js"
web_include_css = "assets/erpnext/css/website.css"

after_install = "erpnext.setup.install.after_install"

boot_session = "erpnext.startup.boot.boot_session"
notification_config = "erpnext.startup.notifications.get_notification_config"

on_session_creation = "erpnext.shopping_cart.utils.set_cart_count"
on_logout = "erpnext.shopping_cart.utils.clear_cart_count"

# website
update_website_context = "erpnext.shopping_cart.utils.update_website_context"
my_account_context = "erpnext.shopping_cart.utils.update_my_account_context"

email_append_to = ["Job Applicant", "Opportunity", "Issue"]

calendars = ["Task", "Production Order", "Time Log", "Leave Application", "Sales Order"]

website_generators = ["Item Group", "Item", "Sales Partner"]

website_context = {
	"favicon": 	"/assets/erpnext/images/favicon.png",
	"splash_image": "/assets/erpnext/images/splash.png"
}

website_route_rules = [
	{"from_route": "/orders", "to_route": "Sales Order"},
	{"from_route": "/orders/<path:name>", "to_route": "order",
		"defaults": {
			"doctype": "Sales Order",
			"parents": [{"title": _("Orders"), "name": "orders"}]
		}
	},
	{"from_route": "/invoices", "to_route": "Sales Invoice"},
	{"from_route": "/invoices/<path:name>", "to_route": "order",
		"defaults": {
			"doctype": "Sales Invoice",
			"parents": [{"title": _("Invoices"), "name": "invoices"}]
		}
	},
	{"from_route": "/shipments", "to_route": "Delivery Note"},
	{"from_route": "/shipments/<path:name>", "to_route": "order",
		"defaults": {
			"doctype": "Delivery Notes",
			"parents": [{"title": _("Shipments"), "name": "shipments"}]
		}
	}
]

has_website_permission = {
	"Sales Order": "erpnext.controllers.website_list_for_contact.has_website_permission",
	"Sales Invoice": "erpnext.controllers.website_list_for_contact.has_website_permission",
	"Delivery Note": "erpnext.controllers.website_list_for_contact.has_website_permission",
	"Issue": "erpnext.support.doctype.issue.issue.has_website_permission"
}

permission_query_conditions = {
	"Contact": "erpnext.utilities.address_and_contact.get_permission_query_conditions_for_contact",
	"Address": "erpnext.utilities.address_and_contact.get_permission_query_conditions_for_address"
}

has_permission = {
	"Contact": "erpnext.utilities.address_and_contact.has_permission",
	"Address": "erpnext.utilities.address_and_contact.has_permission"
}

dump_report_map = "erpnext.startup.report_data_map.data_map"

before_tests = "erpnext.setup.utils.before_tests"

standard_queries = {
	"Customer": "erpnext.selling.doctype.customer.customer.get_customer_list"
}

doc_events = {
	"Stock Entry": {
		"on_submit": "erpnext.stock.doctype.material_request.material_request.update_completed_and_requested_qty",
		"on_cancel": "erpnext.stock.doctype.material_request.material_request.update_completed_and_requested_qty"
	},
	"User": {
		"validate": "erpnext.hr.doctype.employee.employee.validate_employee_role",
		"on_update": "erpnext.hr.doctype.employee.employee.update_user_permissions"
	},
	"Purchase Invoice": {
		"validate": "erpnext.selling.custom_methods.validate_batch",
		"on_submit": ["erpnext.selling.custom_methods.create_batchwise_price_list","erpnext.selling.custom_methods.update_item_price_rate_pi"],
		"on_cancel": ["erpnext.selling.custom_methods.cancel_batchwise_price_list","erpnext.selling.custom_methods.update_item_price_on_pi_cl"]
	},
	"Quotation": {
		"on_update": "erpnext.selling.custom_methods.validate_price_list"
	},
	"Supplier Quotation":{
		"on_submit":"erpnext.selling.custom_methods.update_item_price_sq",
		"on_cancel":"erpnext.selling.custom_methods.update_item_price_on_sq_cl"
	},
	"Item Price":{
		"on_update":"erpnext.selling.custom_methods.update_item_price_ip"
	},
	"Item":{
		"validate":["erpnext.selling.custom_methods.check_eq_item_selected_twice","erpnext.selling.custom_methods.delete_eq_item_entry"],
		"on_update":["erpnext.selling.custom_methods.auto_create_self_item_entry","erpnext.selling.custom_methods.create_eq_item_entry"]
	},
	"Delivery Note":{
		"on_update":"erpnext.selling.custom_methods.update_sales_item_name"
	},
	"Sales Taxes and Charges Template": {
		"on_update": "erpnext.shopping_cart.doctype.shopping_cart_settings.shopping_cart_settings.validate_cart_settings"
	},
	"Price List": {
		"on_update": "erpnext.shopping_cart.doctype.shopping_cart_settings.shopping_cart_settings.validate_cart_settings"
	},
}

scheduler_events = {
	"hourly": [
		"erpnext.controllers.recurring_document.create_recurring_documents"
	],
	"daily": [
		"erpnext.stock.reorder_item.reorder_item",
		"erpnext.setup.doctype.email_digest.email_digest.send",
		"erpnext.support.doctype.issue.issue.auto_close_tickets",
		"erpnext.accounts.doctype.fiscal_year.fiscal_year.auto_create_fiscal_year",
		"erpnext.hr.doctype.employee.employee.send_birthday_reminders"
	]
}

default_mail_footer = """<div style="text-align: center;">
	<a href="https://erpnext.com?source=via_email_footer" target="_blank" style="color: #8d99a6;">
		Sent via ERPNext
	</a>
</div>"""

get_translated_dict = {
	("page", "setup-wizard"): "frappe.geo.country_info.get_translated_dict",
	("doctype", "Global Defaults"): "frappe.geo.country_info.get_translated_dict"
}
