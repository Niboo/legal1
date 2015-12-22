# -*- coding: utf-8 -*-
from openerp import api, models


class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    @api.model
    def update_delay(self):
        for info in self:
            tmpl = info.product_tmpl_id
            # While in the cashe, the seller_ids order might not change
            tmpl.refresh()
            if tmpl.seller_ids[0].delay:
                delay = tmpl.seller_ids[0].delay + 1
                if tmpl.sale_delay != delay:
                    tmpl.write({'sale_delay': delay})

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        res = super(SupplierInfo, self).create(vals)
        res.update_delay()
        return res

    @api.multi
    def write(self, vals):
        res = super(SupplierInfo, self).write(vals)
        if 'sequence' in vals or 'delay' in vals:
            self.update_delay()
