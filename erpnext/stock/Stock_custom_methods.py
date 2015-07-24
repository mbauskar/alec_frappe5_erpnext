from __future__ import unicode_literals
import frappe

from frappe.utils import cint, cstr, flt, formatdate
from frappe.model.mapper import get_mapped_doc

from frappe import msgprint, _, throw
from erpnext.setup.utils import get_company_currency
import frappe.defaults
from frappe.desk.form.utils import get_linked_docs
import json

@frappe.whitelist()
def get_items_detail(item_code):
	return [
		frappe.db.get_value('Item',item_code,'item_name'),
		frappe.db.get_value('Item',item_code,'item_group'),
		frappe.db.get_value('Item',item_code,'brand')
	]