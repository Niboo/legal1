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
                if (this.picking.partner_id){
                    res = res + ' - ' + this.picking.partner_id[1];
                }
                if (this.picking.supplier_reference){
                    res = res + ' (' + _t('ref:') + ' ' + this.picking.supplier_reference + ')';
                }
            }
            return res;
        }
    });
}
