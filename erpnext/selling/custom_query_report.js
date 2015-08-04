frappe.require("assets/js/slickgrid.min.js");
var selected_grid_data;
erpnext.selling.CustomQueryReport = erpnext.selling.QuotationController.extend({
    search:function(doc){
        me = this;
        setTimeout(function(){return frappe.call({
          method: "erpnext.selling.custom_methods.get_details",
          args: {doc:me.frm.doc},
          callback: function(r) {
            if(r.message)
            {
              unhide_field('query_report');
              unhide_field('add');
              me.make_grid(r.message,me.frm.doc)
            }
            else{
              hide_field('query_report');
              hide_field('add');
            }
          }
        });},1000)
  },

  make_grid:function(data1,doc){
    var me=this
    var query_report=document.getElementById('dynamic')
    var dataView;
    var grid;
    var data = [];

    var options = {
      editable: true,
      asyncEditorLoading: false,
      autoEdit: false,
      enableCellNavigation: true,
      showHeaderRow: true,
      headerRowHeight: 30,
      rowHeight:25,
      explicitInitialization: true,
      multiColumnSort: true,
      forceFitColumns:true,
      enableColumnReorder: false
    };

    var columnFilters = {};
    columns = me.get_columns(doc)

    // this.waiting = frappe.messages.waiting($(cur_frm.fields_dict.query_report.wrapper).find(".waiting-area").empty().toggle(true),
    //  "Loading Report...");

    function filter(item) {
      for (var columnId in columnFilters) {
        if (columnId !== undefined && columnFilters[columnId] !== "") {
          var c = selected_grid_data.getColumns()[selected_grid_data.getColumnIndex(columnId)];
          if (!me.compare_values(item[c.field],columnFilters[columnId],c)) {
            return false;
          }
        }
      }
      return true;
    }

    $(function () {
      var checkboxSelector = new Slick.CheckboxSelectColumn({
      cssClass: "slick-cell-checkboxsel"
    });
    columns.push(checkboxSelector.getColumnDefinition());

    for (var i = 0; i < data1.length; i++) {
      var d = (data[i] = {});
      d["id"] = i;
      for (var j = 0; j < columns.length; j++) {
        d[j] = data1[i][j];
        if(j==4 && d[j]=='1'){
          d[j] = 'Yes'
        }
        else if(j==4){
         d[j] = 'No'
        }
      }
      d[0]=i+1
    }
    dataView = new Slick.Data.DataView();
    this.grid = new Slick.Grid(query_report, dataView, columns, options);
    var me = this
    dataView.onRowCountChanged.subscribe(function (e, args) {
      me.grid.updateRowCount();
      me.grid.render();
    });

    dataView.onRowsChanged.subscribe(function (e, args) {
      me.grid.invalidateRows(args.rows);
      me.grid.render();
    });


    $(this.grid.getHeaderRow()).delegate(":input", "change keyup", function (e) {
      var columnId = $(this).data("columnId");
      if (columnId != null) {
        columnFilters[columnId] = $.trim($(this).val());
        dataView.refresh();
      }
    });

    this.grid.onHeaderRowCellRendered.subscribe(function(e, args) {
        $(args.node).empty();
        $("<input type='text'>")
           .data("columnId", args.column.id)
           .val(columnFilters[args.column.id])
           .appendTo(args.node);
    });

    this.grid.init();

    dataView.beginUpdate();
    dataView.setItems(data);
    dataView.setFilter(filter);
    dataView.endUpdate();
    this.grid.setSelectionModel(new Slick.RowSelectionModel({selectActiveRow: false}));
    this.grid.registerPlugin(checkboxSelector);
    this.grid.onSort.subscribe(function (e, args) {
      var cols = args.sortCols;
      data.sort(function (dataRow1, dataRow2) {
        for (var i = 0, l = cols.length; i < l; i++) {
          var field = cols[i].sortCol.field;
          var sign = cols[i].sortAsc ? 1 : -1;
          var value1 = dataRow1[field], value2 = dataRow2[field];
          var result = (value1 == value2 ? 0 : (value1 > value2 ? 1 : -1)) * sign;
          if (result != 0) {
            return result;
          }
        }
          return 0;
      });
      for (k=0;k<data.length;k++)
      {
        data[k][0]=k+1
      }
      dataView.setItems(data);
    });
      var columnpicker = new Slick.Controls.ColumnPicker(columns, this.grid, options);
      selected_grid_data = this.grid
    })

  },
  compare_values: function(value, filter, columnDef) {
    var invert = false;
    value = value + "";
    value = value.toLowerCase();
    filter = filter.toLowerCase();
    out = value.indexOf(filter) != -1;

    if(invert)
      return !out;
    else
      return out;
  },

  get_columns:function(doc){
    var columns = [];
    if (doc.item_groups){
      columns = [
       {id: "0", name: "Sr", field: "0",width:40, sortable: true},
       {id: "1", name: "Quote Item", field: "1",width:100, sortable: true},
       {id: "2", name: "Brand", field: "2",width:80, sortable: true},
       {id: "3", name: "Performance", field: "3",width:120, sortable: true},
       {id: "4", name: "Previously Ordered", field: "4",width:70, sortable: true},
       {id: "5", name: "Batch", field: "5",width:80, sortable: true},
       {id: "6", name: "Rate", field: "6",width:100, sortable: true},
       {id: "7", name: "Actual Qty", field: "7",width:100, sortable: true}
      ]
    }
    else {
      columns = [
       {id: "0", name: "Sr", field: "0",width:40, sortable: true},
       {id: "1", name: "Quote Item", field: "1",width:100, sortable: true},
       {id: "2", name: "Brand", field: "2",width:80, sortable: true},
       {id: "3", name: "Item Group", field: "3",width:120, sortable: true},
       {id: "4", name: "Previously Ordered", field: "4",width:70, sortable: true},
       {id: "5", name: "Batch", field: "5",width:80, sortable: true},
       {id: "6", name: "Rate", field: "6",width:100, sortable: true},
       {id: "7", name: "Actual Qty", field: "7",width:100, sortable: true}
      ]
    }
    return columns
  },
  add:function(doc,cdt,cdn){
    var me = this;
    var selectedData = []
    selectedIndexes=selected_grid_data.getSelectedRows();
    jQuery.each(selectedIndexes, function (index, value) {
      selectedData.push(selected_grid_data.getData().getItem(value));
    });
    if(selectedData){
      return get_server_fields('get_item_details', selectedData, '', doc, cdt, cdn, 1,function(){
        refresh_field('items')
      });
    }
  }
})

frappe.ui.form.on("Quotation", "validate", function(doc, cdt, cdn) {
    hide_field(['query_report', 'add'])
});


cur_frm.fields_dict.item_groups.get_query=function(){
  return {
    filters: {
      "show_in_website": 1
    }
  }
}

