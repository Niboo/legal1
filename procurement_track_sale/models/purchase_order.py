from openerp import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def action_show_procurements(self):
        result = self.env['product.template']._get_act_window_dict(
            'procurement.procurement_exceptions')
        result['domain'] = [('purchase_line_id.order_id', 'in', self.ids)]
        return result

    qty_procurements = fields.Integer(compute="_get_qty_procurements")

    @api.multi
    def _get_qty_procurements(self):
        for order in self:
            order.qty_procurements = len(  # count argument is often ignored
                self.env['procurement.order'].search(
                    [('purchase_line_id.order_id', '=', order.id)]))
