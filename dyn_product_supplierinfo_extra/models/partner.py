# -*- coding: utf-8 -*-
from openerp import fields, models


class res_partner(models.Model):
    _inherit = 'res.partner'

    supplier_delay_default = fields.Integer('Default Delivery Lead Time')
