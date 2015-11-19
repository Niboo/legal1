openerp.dyn_picking_partner_reference = function(instance){
    module = instance.stock,
    _t = instance.web._t;

    /* the stock wizard won't be initialized at this point, so we work on the
       prototype. That means extend instead of include. */

    module.PickingMainWidget = module.PickingMainWidget.extend({
        // Give picking label more space on a medium size viewport
        get_header: function(picking_id){
            res = '';
            if(this.picking){
                res = this.picking.name;
                if(this.picking.origin){
                    res = res + ' - ' + this.picking.origin.split(":")[0];
                }
                if(this.picking.partner_id){
                    res = res + ' - ' + this.picking.partner_id[1];
                }
                if(this.picking.supplier_reference){
                    res = res + ' (' + _t('ref:') + ' ' + this.picking.supplier_reference + ')';
                }
            }
            return res;
        },

        barcode_notify: function(msg) {
            var el = this.$el.find('#barcode_notification');
            el.value = msg;
            el.show();
            setTimeout(function() {el.hide()}, 5000);
        },

        scan: function(ean){ //scans a barcode, sends it to the server, then reload the ui
            /* Overwrite this function from core (addons/stock/static/src/widgets.js).
               We add in a notification if the product cannot be found */
            var self = this;
            var product_visible_ids = this.picking_editor.get_visible_ids();
            return new instance.web.Model('stock.picking')
                .call('process_barcode_from_ui', [self.picking.id, ean, product_visible_ids])
                .then(function(result){
                    if (result.filter_loc !== false){
                        //check if we have receive a location as answer
                        if (result.filter_loc !== undefined){
                            var modal_loc_hidden = self.$('#js_LocationChooseModal').attr('aria-hidden');
                            if (modal_loc_hidden === "false"){
                                var line = self.$('#js_LocationChooseModal .js_loc_option[data-loc-id='+result.filter_loc_id+']').attr('selected','selected');
                            }
                            else{
                                self.$('.oe_searchbox').val(result.filter_loc);
                                self.on_searchbox(result.filter_loc);
                            }
                        }
                    }
                    if (result.operation_id !== false){
                        self.refresh_ui(self.picking.id).then(function(){
                            return self.picking_editor.blink(result.operation_id);
                        });
                    }
                    /* Start of local change */
                    else {
                        self.barcode_notify(_t('No product was found for this supplier with code ') + ean);
                    }
                    /* End of local change */
                });
        },

    });
}
