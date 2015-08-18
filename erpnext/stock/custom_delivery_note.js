erpnext.stock.CustomDeliveryNote = erpnext.stock.DeliveryNoteController.extend({
  init:function(doc,dt,dn){
    this.doc = doc
  }
});

cur_frm.cscript.get_alternative_items= function(doc,cdt,cdn){
     var dialog = new frappe.ui.Dialog({
        title:__('Alternative Items'),
        fields: [
          {fieldtype:'HTML', fieldname:'alt_item_name', label:__(''), reqd:false,
            description: __(""), options:"<div class='class_Name' style='width:100%;max-height:400px;overflow:auto'></div>"},
          {fieldtype:'Button', fieldname:'get_item_details', label:__('Ok') }
          ]
        })
      var fd = dialog.fields_dict;
      $(fd.get_item_details.input).closest('div').css("padding-top","15px")
      if (doc.items){
        frappe.call({
            method:"erpnext.selling.custom_methods.get_alternative_item_details",
            args:{"doc":doc},
            callback:function(r){
              console.log(r)
                    //Get data from server and Render it on dialog
                    var me = this;
                     var result_set =r.message[0]
                     var qty_set = r.message[1]
                     console.log(result_set)
                     alter_dic={}
                     //Render Result on Dialog
                     $.each(result_set,function(i,d){
                        if (d.length!=0){
                          me.table = $("<form><table class='table table-bordered' id='mytable' width=80%>\
                            <thead class='grid-heading-row'>\
                            <tr><th colspan='2' style='align:center'>DN Item : "+i+"</th>\
                            <th>Quantity : "+qty_set[i]+"</th></tr>\
                            <tr><th></th><th style='text-align:center'>Item</th><th style='text-align:center'>Stock Level</th></tr>\
                            </thead><tbody></tbody>\
                            </table></form><br>").appendTo($('.class_Name'))
                          $.each(d,function(key,val){
                              var row = $("<tr>").appendTo(me.table.find("tbody"));
                               $("<td class='row'>").html('<input type="radio" name="sp" id="'+i+'">')
                                  .attr("item", val["item_code"])
                                  .attr("qty", val["actual_qty"])
                                  .attr("item_name", val["item_name"])
                                  .attr("manufacturer_pn", val["manufacturer_pn"])
                                  .attr("oem_part_number", val["oem_part_number"])
                                  .attr("description", val["description"])
                                  .attr("warehouse", val["warehouse"])
                                  .attr("stock_uom", val["stock_uom"])
                                .appendTo(row)
                              $("<td class='row' style='height:15px;text-align:center'>").html(''+val["item_code"]+'').appendTo(row);
                              $("<td class='row' align='center' style='height:15px'>").html(''+val["actual_qty"]+'').appendTo(row);
                          })

                        }
                        /*else{
                          $('<div><b>Alternative Items for '+i+'</b></div></br><div><h5>There is no Stock available of any Equivalent Item</h5></div>').appendTo($(fd.alt_item_name.wrapper))
                        }*/
                  })
                  //show dialog
                  $(".ui-front").css({"max-height":"500px","overflow":"auto"})
                  $(".btn-primary").css("width","100px")
                  $(".empty-form-alert").remove();
                  dialog.show();

                  $("input[name='sp']").change(function () {
                        alter_dic[$(this).attr('id')]={"item_code":$(this).closest('td').attr("item"),"qty":$(this).closest('td').attr("qty"),"item_name":$(this).closest('td').attr("item_name"),"manufacturer_pn":$(this).closest('td').attr("manufacturer_pn"),"oem_part_number":$(this).closest('td').attr("oem_part_number"),"description":$(this).closest('td').attr("description"),"warehouse":$(this).closest('td').attr("warehouse"),"stock_uom":$(this).closest('td').attr("stock_uom")}
                  })

                  $(fd.get_item_details.input).click(function(){

                       $.each(doc.items,function(i,d){
                            if (alter_dic[d.item_code]){
                                original_item=d.item_code
                                alter_item=alter_dic[d.item_code]
                                d.item_code = alter_item["item_code"]
                                d.item_name = alter_item["item_name"]
                                d.manufacturer_pn = alter_item["manufacturer_pn"]
                                d.description = alter_item["description"]
                                d.old_oem = d.current_oem
                                d.current_oem = alter_item["oem_part_number"]
                                d.stock_uom = alter_item["stock_uom"]
                                d.sales_item_name = d.item_code
                                if (alter_dic[original_item]["qty"] < d.qty){
                                  d.actual_qty =alter_item["qty"]
                                }
                                if (alter_item["oem_part_number"] !=  d.old_oem){
                                  d.oem_part_number = alter_item["oem_part_number"]+"(Same as "+(d.old_oem)+")"
                                }
                                else{
                                  d.oem_part_number = alter_item["oem_part_number"]
                                }

                          }
                      })
                    dialog.hide()
                    refresh_field('items')
                    cur_frm.save()
                })
          }
      })
    }
}

frappe.ui.form.on("Delivery Note Item", "item_code", function(doc, cdt, cdn) {
    var d = locals[cdt][cdn]
    d.sales_item_name = d.item_code
    refresh_field('sales_item_name')
});
{% include 'frappe_subscription/frappe_subscription/delivery_note.js' %}
//
// cur_frm.cscript.get_packing_details = function(doc,cdt,cdn){
//     return frappe.call({
//         method: "frappe_subscription.bin_packing.get_bin_packing_details",
//         args:{
//             delivery_note:doc.name,
//             // items:doc.items
//         },
//         callback: function(r){
//             if(!r.exc) {
//                 // refresh_field("packing_slip_details");
//                 cur_frm.reload_doc();
//                 frappe.msgprint("Packing Slip Created");
//             }
//         }
//     });
// }
