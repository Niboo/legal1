from openerp import models, fields, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def _get_sale_reference(self):
        for line in self:
            line.sale_reference = ','.join(
                line.mapped(
                    'procurement_ids.ultimate_sale_line_id'
                    '.order_id.name')) or False

    sale_reference = fields.Char(
        compute='_get_sale_reference')
