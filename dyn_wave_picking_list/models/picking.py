# -*- coding: utf-8 -*-
from openerp import fields, models


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    packages_assigned = fields.Boolean(
        'Packages Have Been Assigned', required=False)
    box_nbr = fields.Integer('Box #')
