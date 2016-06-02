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

from openerp import models, fields, api


class StockPicking(models.Model):

    _inherit = "stock.picking"

    priority_weight = fields.Float("Priority",
                                   compute='set_priority_weight',
                                   store=True)

    @api.multi
    @api.depends('group_id')
    def set_priority_weight(self):
        for picking in self:
            sale = self.env['sale.order'].search([
                ('procurement_group_id', '=', picking.group_id.id),
                ('procurement_group_id', '!=', False)
            ])

            if sale and (sale.priority_weight or sale.priority_weight_computed):
                picking.priority_weight = \
                    sale.priority_weight or sale.priority_weight_computed
