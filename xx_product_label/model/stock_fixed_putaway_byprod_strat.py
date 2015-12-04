#-*- coding: utf-8 -*-
from openerp import models, api


class PutawayByprod(models.Model):
    _inherit = 'stock.fixed.putaway.byprod.strat'

    @api.multi
    def print_label(self):
        self.ensure_one()
        return self.with_context(
            destination=self.fixed_location_id.name
        ).product_id.action_print_product_barcode()
