from openerp import fields, models


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    supplier_id = fields.Many2one('res.partner', 'Supplier', related='purchase_id.partner_id', store=True)
