cur_frm.cscript.engine_compatibility__remove = function (doc,cdt,cdn){
  frappe.call({
    	method:"erpnext.selling.custom_methods.get_item_code",
    	args:{"row_name":cdn},
    	callback:function(r){
    		if (!doc.deleted_eq_item){
    			doc.deleted_eq_item = r.message
    		}else{
    			doc.deleted_eq_item = doc.deleted_eq_item+','+r.message
    		}    		
    		refresh_field('deleted_eq_item')
    	}
    })
}

frappe.ui.form.on("Item", "refresh", function(doc, cdt, cdn) {
    refresh_field('engine_compatibility_')   
});

frappe.ui.form.on("Item", "validate", function(doc, cdt, cdn) {
    setTimeout(function(){
      refresh_field(['deleted_eq_item','engine_compatibility_'])},2000)
});

frappe.ui.form.on("Quote Item", "item_code", function(doc, cdt, cdn) {
    var d=locals[cdt][cdn]
    frappe.call({
        method:"erpnext.stock.Stock_custom_methods.get_items_detail",
        args:{"item_code":d.item_code},
        callback:function(r){
            if(r.message){
                d.item_name= r.message[0]
                d.item_group=r.message[1]
                d.brand=r.message[2]
                refresh_field('engine_compatibility_')
            }
        }
    })
});
