cur_frm.cscript.generate_po=function(doc,dt,dn){
	frappe.call({
			method: 'erpnext.selling.custom_methods.generate_po',
			
	});
}
cur_frm.cscript.generate_sq=function(doc,dt,dn){
	frappe.call({
			method:'erpnext.selling.custom_methods.create_supplier_quotation',
});

}
