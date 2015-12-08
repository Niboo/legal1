# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Dynapps (<http://dynapps.be>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
from openerp import models, fields, api


class Product(models.Model):
    _inherit = 'product.product'

    qty_putaway = fields.Integer(compute="_get_qty_putaway")
    putaway_ids = fields.One2many(
        'stock.fixed.putaway.byprod.strat',
        'product_id', string='Putaway locations by product')

    @api.multi
    def get_putaway_location(self):
        """ For a single product, return the putaway location. Used as a
        lookahead at picking IN time. """
        self.ensure_one()
        strats_by_prod = self.env['stock.fixed.putaway.byprod.strat'].search(
            [('product_id', '=', self.id)], limit=1)
        if strats_by_prod:
            return strats_by_prod.fixed_location_id
        categ = self.categ_id
        categ_ids = [categ.id]
        while categ.parent_id:
            categ_ids.append(categ.parent_id.id)
            categ = categ.parent_id
        strats = self.env['stock.fixed.putaway.strat'].search(
            [('category_id', 'in', categ_ids)], limit=1)
        if strats:
            return strats.fixed_location_id
        return self.env.ref('putaway_apply.default_temp_location')

    @api.multi
    def _get_qty_putaway(self):
        for product in self:
            product.qty_putaway = self.env[
                'stock.fixed.putaway.byprod.strat'].search(
                [('product_id', 'in', self.ids)], count=True)

    @api.multi
    def action_product_putaway(self):
        result = self.product_tmpl_id._get_act_window_dict(
            'putaway_apply.action_product_putaway_location')
        result['domain'] = "[('product_id', 'in', [%s])]" % (
            ', '.join([str(res_id) for res_id in self.ids]))
        result['context'] = "{'default_product_id': %s}" % (
            self.ids[0] if self.ids else 'False')
        return result


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    qty_putaway = fields.Integer(compute="_get_qty_putaway")

    @api.multi
    def _get_qty_putaway(self):
        for template in self:
            template.qty_putaway = self.env[
                'stock.fixed.putaway.byprod.strat'].search(
                [('product_id.product_tmpl_id', 'in', self.ids)], count=True)

    @api.multi
    def action_product_putaway(self):
        result = self._get_act_window_dict(
            'putaway_apply.action_product_putaway_location')
        result['domain'] = "[('product_id.product_tmpl_id', 'in', [%s])]" % (
            ', '.join([str(res_id) for res_id in self.ids]))
        result['context'] = "{'default_product_id': %s}" % (
            self.product_variant_ids[0].id
            if self.product_variant_ids else False)
        return result
