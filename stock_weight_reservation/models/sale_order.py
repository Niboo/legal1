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

    priority_weight = fields.Float("Priority")
    priority_weight_computed = fields.Float("Priority (computed)",
                                              compute="_compute_weight")

    @api.multi
    @api.depends('order_line')
    def _compute_weight(self):
        for order in self:
            weight = 0
            # compute the number of items
            for line in order.order_line:
                weight += line.product_uos_qty
            order.priority_weight_computed = weight

    @api.multi
    def action_button_confirm(self):
        value = super(SaleOrder, self).action_button_confirm()
        for picking in self.picking_ids:
            picking.priority_weight = self.priority_weight or self.priority_weight_computed
        return value

    @api.constrains('priority_weight')
    def _check_priority_weight(self):
        for picking in self.picking_ids:
            picking.priority_weight = self.priority_weight
