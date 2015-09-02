from __future__ import unicode_literals
import frappe

from frappe.utils import cint, cstr, flt, formatdate
from frappe.model.mapper import get_mapped_doc

from frappe import msgprint, _, throw
from erpnext.setup.utils import get_company_currency
import frappe.defaults
from frappe.desk.form.utils import get_linked_docs
import json

#check batch is of respective item code
def validate_batch(doc,method):
	for d in doc.get('items'):
		if d.batch_no and d.item_code != frappe.db.get_value('Batch',d.batch_no,'item'):
			frappe.throw(_("Select batch respective to item code {0}").format(d.item_code))

#maintain supplier name,rate,batch as EC-Rate of purchase
def create_batchwise_price_list(doc, method):
	for d in doc.get('items'):
		item_price=frappe.db.get_value('Item Price',{'item_code':d.item_code,'price_list':'EC - Rate of Purchase'},'name')
		if not item_price:
			create_item_price(d,doc)
		else:
			create_batchwise_item_price(item_price,d,doc)
#create item price list
def create_item_price(d,doc):
	pl=frappe.new_doc('Item Price')
	pl.price_list='EC - Rate of Purchase'
	pl.buying = 1
	pl.selling = 1
	pl.item_code= d.item_code
	pl.price_list_rate=d.rate
	pl.item_name=d.item_name
	pl.item_description=d.description
	pl.currency=doc.currency
	pl.save(ignore_permissions=True)
	create_batchwise_item_price(pl.name,d,doc)

#create batch wise price list rate
def create_batchwise_item_price(name, d, doc):
	if d.batch_no and not frappe.db.get_value('Batchwise Purchase Rate',{'batch':d.batch_no},'name'):
		bpr=frappe.new_doc('Batchwise Purchase Rate')
		bpr.supplier=doc.supplier
		bpr.batch=d.batch_no
		bpr.rate=d.rate
		bpr.parentfield='batchwise_purchase_rate'
		bpr.parenttype='Item Price'
		bpr.parent=name
		bpr.document = doc.name
		bpr.save(ignore_permissions=True)

#on cancel delete created price list
def cancel_batchwise_price_list(doc, method):
	for d in doc.get('items'):
		if d.batch_no:
			frappe.db.sql("delete from `tabBatchwise Purchase Rate` where document='%s'"%(doc.name))

#create supplier quotation from quotationin draft
@frappe.whitelist()
def create_supplier_quotation():
	Quotations=get_quotation_in_draft()
	if Quotations:
		for quotation in Quotations:
			if not frappe.db.get_value("Quotation Used",{"quotation":quotation[0]},"quotation"):
				items=frappe.db.sql("""select item_code,qty from `tabQuotation Item` where parent='%s'"""%(quotation[0]),as_list=1)
				for item in items:
					item_price_exists=frappe.db.sql("""select distinct ifnull(price_list_rate,0) from `tabItem Price` where item_code='%s' """%(item[0]))
					if not item_price_exists or item_price_exists[0][0]==0:
						suppliers=get_suplier_details(item[0])
						if suppliers:
							for supplier in suppliers:
								make_supplier_quotation(item,supplier[0])
				update_used_quotation(quotation[0])

#get all quotations in draft state
def get_quotation_in_draft():
	return frappe.db.sql("""select name from `tabQuotation` where docstatus=0""",as_list=1)

#get all quotations that were used during last scheduler event for validation
def get_quotation_used(quotation):
	return frappe.db.sql("""select quotation from `tabQuotation Used` where quotation='%s'"""%(quotation),as_list=1)

#get details of supplier
def get_suplier_details(item):
	item_wrapper = frappe.get_doc("Item", item)
	return frappe.db.sql("""select supplier_name from `tabSupplier` where supplier_name in(select parent from `tabSupplier Brands` where brand='%s') and
		supplier_name in(select parent from `tabSupplier Item Groups` where item_group='%s')"""%(item_wrapper.brand,item_wrapper.item_group),as_list=1)


#create supplier quotation
def make_supplier_quotation(item,supplier):
	quotation_exists=check_quotation_exists(supplier)
	if quotation_exists:
		if not frappe.db.get_value('Supplier Quotation Item',{'item_code':item[0],'parent':quotation_exists},'name'):
			update_supplier_items(item,quotation_exists)
		else:
			update_qty_quotation(quotation_exists ,item)
	else:
		new_supplier_quotaion(supplier,item)


#check if quotation exists in for supplier
def check_quotation_exists(supplier):
	return frappe.db.get_value('Supplier Quotation',{'supplier':supplier,'docstatus':0},'name')

#create new supplier quotation
def new_supplier_quotaion(supplier,item):
	item_wrapper = frappe.get_doc("Item", item[0])
	sq=frappe.new_doc('Supplier Quotation')
	sq.supplier=supplier
	sq.append("items", {
						"doctype": "Supplier Quotation Item",
						"item_code": item[0],
						"item_name": item_wrapper.item_name,
						"description": item_wrapper.description,
						"uom": item_wrapper.stock_uom,
						"item_group": item_wrapper.item_group,
						"brand": item_wrapper.brand,
						"qty": item[1],
						"base_rate":0,
						"base_amount":0,
						"manufacturer_pn":item_wrapper.manufacturer_pn,
						"oem_part_number":item_wrapper.oem_part_number
						})
	sq.save(ignore_permissions=True)

#Add item to existing supplier quotation
def update_supplier_items(item,name):
	item_wrapper = frappe.get_doc("Item", item[0])
	idx=frappe.db.sql("""select ifnull(max(idx),0)+1 as idx from `tabSupplier Quotation Item` where parent='%s'"""%(name),as_list=1)
	sqi=frappe.new_doc('Supplier Quotation Item')
	sqi.idx=idx[0][0]
	sqi.item_code=item[0]
	sqi.item_name=item_wrapper.item_name
	sqi.description=item_wrapper.description
	sqi.manufacturer_pn=item_wrapper.manufacturer_pn
	sqi.oem_part_number=item_wrapper.oem_part_number
	sqi.uom=item_wrapper.stock_uom
	sqi.brand=item_wrapper.brand
	sqi.qty=item[1]
	sqi.base_rate=0
	sqi.base_amount=0
	sqi.item_group=item_wrapper.item_group
	sqi.parentfield='items'
	sqi.parenttype='Supplier Quotation'
	sqi.parent=name
	sqi.save(ignore_permissions=True)

#if item in supplier quotation exists update qty
def update_qty_quotation(name,item):
	frappe.db.sql("""update `tabSupplier Quotation Item` set qty=qty+%s where parent='%s' and item_code='%s'"""%(item[1],name,item[0]))

#when quotation used so it can be negleted in future
def update_used_quotation(quotation):
	if not frappe.db.get_value("Quotation Used",{"quotation":quotation},"quotation"):
		uq=frappe.new_doc('Used Quotation')
		uq.save(ignore_permissions=True)
		qu=frappe.new_doc('Quotation Used')
		qu.quotation=quotation
		qu.parentfield='quotation_used'
		qu.parenttype='Used Quotation'
		qu.parent=uq.name
		qu.save(ignore_permissions=True)

#returns query data
@frappe.whitelist()
def get_details(doc):
	import json
	doc = json.loads(doc)
	condition=get_query(doc)
	result = frappe.db.sql(condition,as_list=1)
	data = previous_ordered_status(doc, result)
	return data

#check whether item previously ordered
@frappe.whitelist()
def previous_ordered_status(doc, result):
	query_data = []
	for data in result:
		for q in range(0,len(data)):
			item = data[1]
			if q == 4:
				if not doc.get('previously_ordered_only'):
					data[q] = get_status(doc, item)
				else:
					data[q] = 1
		query_data.append(data)
	return query_data

#get document status
@frappe.whitelist()
def get_status(doc, item):
	data = 0
	status = frappe.db.sql(""" select ifnull(`tabSales Order`.docstatus,0) from `tabSales Order`, `tabSales Order Item` where `tabSales Order`.name= `tabSales Order Item`.parent
		and `tabSales Order`.customer='%s'
		and `tabSales Order Item`.item_code='%s'
		and `tabSales Order`.docstatus=1 """%(doc.get('customer'),item))
	if status:
		data = 1
	return data

#build query
@frappe.whitelist()
def get_query(doc):
	column = get_columns(doc)
	table = get_tables(doc)
	condition = get_conditions(doc)
	return column + ' ' + table + ' ' + condition

#build columns
@frappe.whitelist()
def get_columns(doc):
	column = 'ifnull(`tabItem`.item_group,"")'
	if doc.get('item_groups'):
		column = 'ifnull(`tabWebsite Item Group`.performance,"")'

	return """  select DISTINCT '',ifnull(`tabQuote Item`.item_code,"") ,
				ifnull(`tabQuote Item`.brand,"") ,
				"""+column+""",
				'',
				ifnull(`tabBatchwise Purchase Rate`.batch,""),
				format(ifnull(`tabBatchwise Purchase Rate`.rate,(select price_list_rate from `tabItem Price` where price_list='EC - Rate of Purchase' and item_code=`tabQuote Item`.item_code)),2) ,
				(select format(ifnull(sum(actual_qty),0),2) from `tabStock Ledger Entry` where item_code=`tabQuote Item`.item_code and batch_no=`tabBatchwise Purchase Rate`.batch)"""

#returns tables required
@frappe.whitelist()
def get_tables(doc):
	table = """ `tabItem` INNER JOIN `tabQuote Item` ON
   		`tabQuote Item`.parent = `tabItem`.name """
	if doc.get('item_groups') and doc.get('part_no'):
		table = """ `tabItem` INNER JOIN `tabQuote Item` ON
		`tabQuote Item`.parent = `tabItem`.name INNER JOIN
		`tabWebsite Item Group` ON `tabQuote Item`.parent = `tabWebsite Item Group`.parent """
	elif doc.get('item_groups'):
		table = """ `tabWebsite Item Group` INNER JOIN `tabQuote Item` ON
   		`tabQuote Item`.parent = `tabWebsite Item Group`.parent"""

   	return """  FROM """+table+""" LEFT JOIN
			   		`tabItem Price` ON `tabQuote Item`.item_code = `tabItem Price`.item_code
				LEFT JOIN
			    	`tabStock Ledger Entry` ON `tabStock Ledger Entry`.item_code = `tabItem Price`.item_code and `tabStock Ledger Entry`.is_cancelled='No'
				LEFT JOIN
					`tabBatchwise Purchase Rate` ON `tabBatchwise Purchase Rate`.parent = `tabItem Price`.name
				LEFT JOIN
			    	`tabSales Order Item` ON `tabSales Order Item`.item_code = `tabQuote Item`.item_code
				LEFT JOIN
			    	`tabSales Order` ON `tabSales Order`.name = `tabSales Order Item`.parent """
#returns conditions for query
@frappe.whitelist()
def get_conditions(doc):
	previous_ordered = condition = '1=1'
	if doc.get('item_groups') and doc.get('part_no'):
		condition = """	`tabItem`.name='%s' and `tabWebsite Item Group`.item_group = '%s' """%(doc.get('part_no'),doc.get('item_groups'))
	elif doc.get('item_groups'):
		condition = """	`tabWebsite Item Group`.item_group = '%s' """%(doc.get('item_groups'))
	elif doc.get('part_no'):
		condition = """	`tabItem`.name='%s' """%(doc.get('part_no'))

	if doc.get('previously_ordered_only') == 1:
		previous_ordered = """`tabSales Order`.customer= '%s' and ifnull(`tabSales Order`.docstatus,0) = 1 """%(doc.get('customer'))

	return """	where """+condition+""" and `tabItem Price`.price_list='EC - Rate of Purchase'
				and """+previous_ordered+""" """

def validate_price_list(doc, method):
	for d in doc.get('items'):
		if d.batch_no:
			rate = frappe.db.sql("select a.rate from `tabBatchwise Purchase Rate` a inner join `tabItem Price` b on a.parent = b.name and b.item_code = '%s' and a.batch = '%s'"%(d.item_code,d.batch_no),as_list=1)
			if rate and flt(rate[0][0]) > flt(d.rate):
				frappe.throw(_('Item Code {0} rate must be greater than rate of price list EC Purchase of Rate').format(d.item_code))

def set_price_list(doc, method):
	doc.competitor = frappe.db.get_value('Price List',doc.price_list,'competitor')
	frappe.db.sql("update `tabItem Price` set competitor=%s where name='%s'"%(cint(doc.competitor),doc.name))

#create purchase orders from submitted sales orders
@frappe.whitelist()
def generate_po():
	sales_orders=get_submitted_sales_orders()
	if sales_orders:
		for sales_order in sales_orders:
			if not frappe.db.get_value("Sales Order Used",{"sales_order":sales_order[0]},"sales_order"):
				doc = frappe.get_doc('Sales Order', sales_order[0])
				for item in doc.get('items'):
					if cint(frappe.db.get_value('Item', item.item_code, 'is_stock_item')) == 1:
						stock_balance=get_stock_balance(item)
						qty = (flt(item.qty) - flt(stock_balance[0][0])) or 0.0
						if flt(qty) > 0.0:
							supplier=get_supplier_details(item.item_code)
							if supplier and supplier[0][1]:
								make_po(supplier,item,sales_order[0], qty)
				update_used(sales_order[0])


#returns submitted sales orders
def get_submitted_sales_orders():
	return frappe.db.sql("""select name from `tabSales Order` where docstatus=1""",as_list=1)

#returns stock balance for item
def get_stock_balance(args):
	return frappe.db.sql("""select actual_qty from `tabBin` where item_code='{0}'
		and warehouse = '{1}'""".format(args.item_code, args.warehouse),as_list=1)

#returns least item price list rate and supplier name
def get_supplier_details(item):
	return frappe.db.sql("""select min(price_list_rate),price_list from `tabItem Price` where item_code='%s' and buying=1 and price_list in (select name from tabSupplier) group by price_list order by price_list_rate limit 1"""%(item),as_list=1)

def get_price_list_rate(item,supplier):
	rate = frappe.db.sql("""select ifnull(price_list_rate,0) from `tabItem Price` where item_code='%s' and buying=1 and price_list='%s'"""%(item,supplier),as_list=1)
	if rate:
		return rate[0][0]
	else:
		return 0
#returns sales orders from which purchase orders created
def get_sales_order_used(sales_order):
	return frappe.db.sql("""select sales_order from `tabSales Order Used` where sales_order='%s'"""%(sales_order[0]),as_list=1)

#makes new po or updates existing
def make_po(supplier,item,sales_order, qty):
	po_exists=check_po_exists(supplier[0][1])
	#price_rate=get_price_list_rate(item[0],supplier[0][1])

	if po_exists:
		item_exists=frappe.db.get_value('Purchase Order Item',{'item_code':item.item_code,'parent':po_exists},'name')
		if not item_exists:
			add_po_items(po_exists,item,sales_order,supplier[0][0], qty)
		else:
			update_qty(po_exists,item,sales_order,supplier[0][0], qty)
	else:
		new_po(supplier,item,supplier[0][0],sales_order, qty)

#check if po exists
def check_po_exists(supplier):
	return frappe.db.get_value('Purchase Order',{'supplier':supplier,'docstatus':0},'name')

#creates new purchase order
def new_po(supplier,item,price_rate,sales_order, qty):
	item_wrapper=frappe.get_doc("Item", item.item_code)
	po=frappe.new_doc('Purchase Order')
	po.supplier=supplier[0][1]
	po.currency = frappe.db.get_value('Supplier', supplier[0][1], 'default_currency') or frappe.db.get_value('Global Defaults', None, 'default_currency')
	po.plc_conversion_rate = frappe.db.get_value('Currency Exchange', {'from_currency': po.currency}, 'exchange_rate')
	po.buying_price_list=supplier[0][1]
	po.append("items", {
					"doctype": "Purchase Order Item",
					"item_code": item.item_code,
					"item_name": item_wrapper.item_name,
					"description": item_wrapper.description,
					"uom": item_wrapper.stock_uom,
					"item_group": item_wrapper.item_group,
					"brand": item_wrapper.brand,
					"qty":qty ,
					"base_rate":0,
					"base_amount":0,
					"manufacturer_pn":item_wrapper.manufacturer_pn,
					"oem_part_number":item_wrapper.oem_part_number,
					"price_list_rate":price_rate,
					"schedule_date":'08-12-2014'
					})

	po.save(ignore_permissions=True)

#maintains sales orders which are used in process
def update_used(sales_order):
	if not frappe.db.get_value("Sales Order Used",{"sales_order":sales_order},"sales_order"):
		uso=frappe.new_doc('Used Sales Order')
		uso.save(ignore_permissions=True)
		sopo=frappe.new_doc('Sales Order Used')
		sopo.sales_order=sales_order
		sopo.parentfield='sales_order_used'
		sopo.parenttype='Used Sales Order'
		sopo.parent=uso.name
		sopo.save(ignore_permissions=True)

#update qty if item in purchase order exists
def update_qty(name,item,sales_order,price_rate, qty):
	frappe.db.sql("""update `tabPurchase Order Item` set qty=qty+%s where parent='%s' and item_code='%s'"""%(qty,name,item.item_code))

#update purchase order with item
def add_po_items(name,item,sales_order,price_rate, qty):
	idx=frappe.db.sql("""select ifnull(max(idx),0)+1 as idx from `tabPurchase Order Item` where parent='%s'"""%(name),as_list=1)
	item_wrapper = frappe.get_doc("Item", item.item_code)
	poi=frappe.new_doc('Purchase Order Item')
	poi.idx=idx[0][0]
	poi.item_code=item.item_code
	poi.item_name=item_wrapper.item_name
	poi.description=item_wrapper.description
	poi.manufacturer_pn=item_wrapper.manufacturer_pn
	poi.oem_part_number=item_wrapper.oem_part_number
	poi.uom=item_wrapper.stock_uom
	poi.brand=item_wrapper.brand
	poi.qty= qty
	poi.price_list_rate=price_rate
	poi.base_rate=0
	poi.base_amount=0
	poi.schedule_date='08-12-2014'
	poi.conversion_factor=1
	poi.item_group=item_wrapper.item_group
	poi.parentfield='items'
	poi.parenttype='Purchase Order'
	poi.parent=name
	poi.save(ignore_permissions=True)

#to make oppurtunity from submitted sales order
@frappe.whitelist()
def make_oppurtunity(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.ignore_pricing_rule = 1
		target.run_method("set_missing_values")


	target_doc = get_mapped_doc("Sales Order", source_name, {
		"Sales Order": {
			"doctype": "Opportunity",
			"validation": {
				"docstatus": ["=", 1]
			}
		},
		"Sales Order Item": {
			"doctype": "Opportunity Item",
			"field_map": {
				"rate": "rate",
				"name": "prevdoc_detail_docname",
				"parent": "against_sales_order",
			},

		}
	}, target_doc, set_missing_values)

	return target_doc

def  update_item_price_rate_pi(doc,method):
	# update the rate if new rate is less than existing item rate
	for item in doc.get('items'):
		if item.item_code:
			rate=get_ec_rate(item.item_code)
			if rate and (item.rate < rate):
				frappe.db.sql("""update `tabItem Price`
					set price_list_rate=%s where item_code='%s'
					and price_list='EC - Rate of Purchase'"""%(item.rate,item.item_code))

def update_item_price_sq(doc,method):
	for d in doc.get('items'):
		rate=get_ec_rate(d.item_code)
		if rate:
			if d.rate < rate:
				frappe.db.sql("""update `tabItem Price`
					set price_list_rate='%s'
					where price_list='EC - Rate of Purchase'
					and item_code='%s' """%(d.rate,d.item_code))
				frappe.db.sql("commit")

def update_item_price_ip(doc,method):
	rate= get_ec_rate(doc.item_code)
	if rate:
		if doc.price_list_rate < rate:
			frappe.db.sql("""update `tabItem Price`
				set price_list_rate='%s' where price_list='EC - Rate of Purchase'
				and item_code='%s' """%(doc.price_list_rate,doc.item_code))
			frappe.db.sql("commit")
		else:
			pass

def get_ec_rate(item_code):
	return frappe.db.get_value("Item Price",{"item_code":item_code,"price_list":"EC - Rate of Purchase"},"price_list_rate")

def update_item_price_on_pi_cl(doc,method):
	for item in doc.get('items'):
		if item.item_code:
			rate=get_rate(item.item_code)
			if rate:
				frappe.db.sql("""update `tabItem Price`
					set price_list_rate=%s
					where item_code='%s'
					and price_list='EC - Rate of Purchase'"""%(rate[0][0],item.item_code))

def update_item_price_on_sq_cl(doc,method):
	for item in doc.get('item_list'):
		if item.item_code:
			rate=get_rate(item.item_code)
			if rate:
				frappe.db.sql("""update `tabItem Price`
					set price_list_rate=%s
					where item_code='%s' and price_list='%s'"""%(rate[0][0],item.item_code,doc.buying_price_list))

def get_rate(item_code):
	return frappe.db.sql("""select least(
		CASE WHEN item_rate = 0 THEN GREATEST(item_rate,quotation_rate,purchase_rate)+1 ELSE item_rate END,
		CASE WHEN quotation_rate= 0 THEN GREATEST(item_rate,quotation_rate,purchase_rate)+1 ELSE quotation_rate END,
		CASE WHEN purchase_rate = 0 THEN GREATEST(item_rate,quotation_rate,purchase_rate)+1 ELSE purchase_rate END) as rate from  (select
		ifnull(min(nullif(ip.price_list_rate,0)),0) as item_rate,
		ifnull(min(nullif(sq.price_list_rate,0)),0) as quotation_rate,
		ifnull(min(nullif(pi.price_list_rate,0)),0) as purchase_rate from `tabItem` im
		left join `tabItem Price` ip on ip.item_code=im.item_code
		left join `tabSupplier Quotation Item` sq on sq.item_code=im.item_code and sq.docstatus=1
		left join `tabPurchase Invoice Item` pi on pi.item_code=im.item_code and pi.docstatus=1
		where im.item_code='%s' group by im.item_code)x"""%(item_code),as_list=1)



def check_eq_item_selected_twice(doc,method):
	item_list = []
	for row in doc.get('engine_compatibility_'):
		if row.item_code in item_list:
			frappe.throw(_("Duplicate entry for Item {0} in Part Equivalency table ").format(row.item_code))
		item_list.append(row.item_code)

def auto_create_self_item_entry(doc,method):
	result = frappe.db.sql(""" select name from `tabQuote Item` where parent='{0}' and  item_code='{1}' """.format(doc.item_code,doc.item_code),as_list=1)
	if not result:
		doc.append('engine_compatibility_',{
		"item_code":doc.item_code,
		"item_name":doc.item_name,
		"brand":doc.brand,
		"item_group":doc.item_group
        })
		doc.save()
		frappe.db.commit()



def create_eq_item_entry(doc,method):
	for row in doc.get('engine_compatibility_'):
		result = frappe.db.sql(""" select name from `tabQuote Item` where parent='{0}' and  item_code='{1}' """.format(row.item_code,doc.item_code),as_list=1)
		if not result:
			item_doc = frappe.get_doc('Item',row.item_code)
			item_doc.append('engine_compatibility_',{
			"item_code":doc.item_code,
			"item_name":doc.item_name,
			"brand":doc.brand,
			"item_group":doc.item_group
            })
			item_doc.save()
			frappe.db.commit()

@frappe.whitelist()
def get_item_code(row_name):
	if row_name:
		return frappe.db.get_value('Quote Item',row_name,'item_code')

def delete_eq_item_entry(doc,method):
	if doc.deleted_eq_item:
		deleted_eq_item = cstr(doc.deleted_eq_item).split(',')
		for d in deleted_eq_item:
			if d != doc.item_code:
				my_doc = frappe.get_doc('Item',d)
				for row in my_doc.get('engine_compatibility_'):
					if row.item_code == doc.item_code:
						my_doc.get('engine_compatibility_').remove(row)
				my_doc.save()
		doc.deleted_eq_item = ''

@frappe.whitelist()
def get_alternative_item_details(doc):
	doc=json.loads(doc)
	item_dict = {}
	alteritem_dic={}
	if doc:
		for d in doc.get('items'):
			result = {}
			if d.get("sales_item_name"):
				result = frappe.db.sql(""" SELECT
						   distinct(qi.item_code),
						   qi.parent,
						   coalesce(bi.actual_qty,0) as actual_qty,
						   ifnull(ite.item_name,'') as item_name,
						   ifnull(ite.manufacturer_pn,'') as manufacturer_pn,
						   ifnull(ite.oem_part_number,'') as oem_part_number,
						   ifnull(ite.description,'') as description,
						   coalesce( bi.warehouse,'') as warehouse,
						   ifnull(ite.stock_uom,'') as stock_uom
						FROM
						   `tabQuote Item` qi  join
						   `tabBin` bi
						on
						   qi.item_code = bi.item_code  join `tabItem` ite
						on
						   ite.item_code = bi.item_code
						where
						qi.parent='{0}'
						AND bi.warehouse='{1}' AND bi.actual_qty!=0  AND qi.item_code!='{2}' """.format(d["sales_item_name"],d["warehouse"],d["sales_item_name"]),as_dict=1)
				alteritem_dic[d["sales_item_name"]]=result
				item_dict[d["sales_item_name"]] = d["qty"]
	return alteritem_dic,item_dict



def update_sales_item_name(doc,method):
	for row in doc.get('items'):
		row.sales_item_name = row.item_code
		row.old_oem = row.current_oem


@frappe.whitelist()
def get_roles_for_so_cancellation():
	role_list = frappe.db.sql("select roles from `tabAssign Roles Permissions`",as_list=1)
	return role_list


@frappe.whitelist()
def custom_get_linked_docs(doctype, name, metadata_loaded=None):
	results = get_linked_docs(doctype,name,metadata_loaded)
	my_dict = make_unique(results)
	cancel_linked_docs(my_dict,doctype,name)
	return 0



def make_unique(results):
	if results:
		for key,value in results.items():
			my_list = []
			for my_key in value:
				if my_key['docstatus'] == 1:
					my_list.append(my_key['name'])
			my_list = list(set(my_list))
			results[key] = my_list
		return results

def cancel_linked_docs(my_dict,doctype,name):
	if my_dict:
		for doc in ['Journal Voucher','Sales Invoice','Packing Slip','Delivery Note']:
			if my_dict.get(doc):
				if doc == 'Sales Invoice':
					check_link_of_sales_invoice(doc,my_dict.get(doc))
				for curr_name in my_dict.get(doc):
					cancel_doc(doc,curr_name)
	cancel_sales_order_self(doctype,name)

def cancel_doc(doc,name):
	my_doc = frappe.get_doc(doc,name)
	my_doc.cancel()



def check_link_of_sales_invoice(doc,si_list):
	for sales_invoice in si_list:
		jv_list = frappe.db.sql(""" select distinct(jvt.parent) from `tabJournal Voucher Detail` jvt  join  `tabJournal Voucher` jv on jv.name=jvt.parent where jvt.against_invoice='{0}' and jv.docstatus= 1  """.format(sales_invoice),as_list=1)
		if jv_list:
				cancel_jv('Journal Voucher',jv_list)

def cancel_jv(doc_name,jv_list):
	for jv in jv_list:
		my_doc = frappe.get_doc(doc_name,jv[0])
		my_doc.cancel()



def cancel_sales_order_self(doctype,name):
	my_doc = frappe.get_doc(doctype,name)
	my_doc.cancel()


@frappe.whitelist()
def set_alternative_item_details(alter_dic,doc):
	if alter_dic:
		alter_dic=json.loads(alter_dic)
		#doc=json.loads(doc)
		c_doc=frappe.get_doc("Delivery Note",doc)
		for d in c_doc.get('items'):
			if alter_dic.has_key(d.item_code):
				original_item=d.item_code
				alter_item=alter_dic.get(d.item_code)["item_code"]
				aitem_doc=frappe.get_doc("Item",alter_item)
				d.item_code = aitem_doc.item_code
				d.item_name = aitem_doc.item_name
				d.manufacturer_pn = aitem_doc.manufacturer_pn
				d.description = aitem_doc.description
				d.old_oem = d.current_oem
				d.current_oem = aitem_doc.oem_part_number
				d.stock_uom = aitem_doc.stock_uom
				d.sales_item_name = d.item_code
				if alter_dic[original_item]["qty"] < d.qty:
					d.actual_qty =alter_dic.get(original_item)["qty"]
				if not (aitem_doc.oem_part_number ==  d.old_oem):
					d.oem_part_number = aitem_doc.oem_part_number
				else:
					d.oem_part_number = cstr(aitem_doc.oem_part_number)+"(Same as %s)"%d.oem_part_number
		c_doc.save(ignore_permissions=True)

	return c_doc
