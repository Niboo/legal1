# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Jerome Guerriat
#    Copyright 2015 Niboo SPRL
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api, fields


class SaleOrder(models.Model):

    _inherit = "sale.order"

    priority = fields.Integer("Priority")

    @api.model
    def create(self, vals):
        if vals.get('priority') == 0 or not vals.get('priority'):
            weight = 0
            for line in vals.get('order_line'):
                weight += line[2]['product_uos_qty']

            vals['priority'] = weight
        return super(SaleOrder, self).create(vals)

    @api.multi
    def action_button_confirm(self):
        value = super(SaleOrder, self).action_button_confirm()
        for picking in self.picking_ids:
            picking.priority = self.priority
        return value
