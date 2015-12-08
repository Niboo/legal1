#-*- coding: utf-8 -*-
from openerp import models, fields, api


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    has_sale_orders = fields.Boolean(compute="_get_has_sale_orders")

    @api.multi
    def _get_has_sale_orders(self):
        for group in self:
            for procurement in group.procurement_ids:
                if procurement.ultimate_sale_line_id:
                    group.has_sale_orders = True
                    break
            else:
                group.has_sale_orders = False

    @api.multi
    def do_view_sale_order(self):
        sale_orders = self.env['sale.order']
        for group in self:
            for procurement in group.procurement_ids:
                order = procurement.ultimate_sale_line_id.order_id
                if order and order not in sale_orders:
                    sale_orders += procurement.ultimate_sale_line_id.order_id
        if not sale_orders:
            return False
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form' if len(sale_orders) == 1 else 'tree,form',
            'res_id': sale_orders.id if len(sale_orders) == 1 else False,
            'domain': [('id', 'in', sale_orders.ids)],
        }
