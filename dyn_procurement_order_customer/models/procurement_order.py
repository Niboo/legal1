from openerp import fields, models


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    customer_id = fields.Many2one('res.partner', 'Customer', related='sale_line_id.order_id.partner_id', store=True)
