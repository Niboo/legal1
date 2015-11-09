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
from openerp import models, api


class Product(models.Model):
    _inherit = 'product.product'

    @api.multi
    def is_temp_location(self):
        """
        For a single product, return whether the putaway strategy that will
        be applied refers to the temp location. Lookahead of the same logic
        that is enforced elsewhere in this module. If no fixed location is
        defined on the product or category, default to True """
        self.ensure_one()
        temp_location = self.env.ref(
            'putaway_apply.default_temp_location')
        strats_by_prod = self.env['stock.fixed.putaway.byprod.strat'].search(
            [('product_id', '=', self.id)], limit=1)
        if strats_by_prod:
            return strats_by_prod.fixed_location_id == temp_location
        categ = self.categ_id
        categ_ids = [categ.id]
        while categ.parent_id:
            categ_ids.append(categ.parent_id.id)
            categ = categ.parent_id
        strats = self.env['stock.fixed.putaway.strat'].search(
            [('category_id', 'in', categ_ids)], limit=1)
        if strats:
            return strats.fixed_location_id == temp_location
        return True
