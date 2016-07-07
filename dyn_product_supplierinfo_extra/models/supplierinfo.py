# -*- coding: utf-8 -*-
from openerp import fields, models, api


class product_supplierinfo(models.Model):
    _inherit = 'product.supplierinfo'
    
    unpack = fields.Boolean("Unpack")
    
    @api.onchange('name')
    def onchange_supplier(self):
        self.delay = self.name.supplier_delay_default
