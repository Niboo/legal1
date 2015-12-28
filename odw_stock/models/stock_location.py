from openerp import fields, models


class Location(models.Model):
    _inherit = 'stock.location'

    name = fields.Char(translate=False)
