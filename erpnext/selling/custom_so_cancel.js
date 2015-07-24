erpnext.selling.CustomSoCancel = frappe.ui.form.Controller.extend({





});	

cur_frm.cscript.cancel_sales_order = function(){

			frappe.confirm(__('All documents linked {eg. Journal Voucher,Sales invoice,Delivery Note} with this Sales Order will be cancelled. Continue?'),
			function() {

			return  frappe.call({
				method:"erpnext.selling.custom_methods.custom_get_linked_docs",
				args: {
					"doctype": cur_frm.doctype,
					"name": cur_frm.docname,
					"metadata_loaded": ''
				},
		            callback:function(r){
		            	window.location.reload()
         
	                 	}
	           })
			}
		);



					

}