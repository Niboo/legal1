from openerp import models, fields, api, _


class Purchase(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def action_picking_create(self):
        picking_ids = []
        for order in self:
            for order_line in order.order_line:
                picking_vals = {
                    'picking_type_id': order.picking_type_id.id,
                    'partner_id': order.partner_id.id,
                    'date': order.date_order,
                    'origin': order.name
                }
                picking_id = self.env['stock.picking'].create(picking_vals)
                order._create_stock_moves(order,[order_line], picking_id.id)
                picking_ids.append(picking_id)
        return picking_ids
