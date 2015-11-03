# -*- coding: utf-8 -*-
from openerp import fields, models


class product_template(models.Model):
    _inherit = 'product.template'

    orderpoint_count = fields.Integer('Reordering Rules', compute="_count_reordering_rules")

    def _count_reordering_rules(self):
        for rec in self:
            pp_ids = self.product_variant_ids.ids
            rec.orderpoint_count = self.env['stock.warehouse.orderpoint'].search_count([('product_id', 'in', pp_ids)])


class product_product(models.Model):
    _inherit = 'product.product'

    orderpoint_count = fields.Integer('Reordering Rules', compute="_count_reordering_rules")

    def _count_reordering_rules(self):
        for rec in self:
            rec.orderpoint_count = self.env['stock.warehouse.orderpoint'].search_count([('product_id', '=', rec.id)])
