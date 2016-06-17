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


class PackingOrder(models.Model):

    _name = "stock.packing.order"

    reference = fields.Char("Reference")
    note = fields.Char("Note")
    stock_move_ids = fields.One2many('stock.move', 'packing_order_id',
                                     string="Related Stock Moves")

    user_id = fields.Many2one('res.users', string="User")
    creation_time = fields.Datetime("Created on")
    write_time = fields.Datetime("Last Written on")


    @api.multi
    def create(self, vals):
        vals['reference'] = self.env['ir.sequence'].get('stock.packing.order')
        vals['creation_time'] = fields.Datetime.now()
        vals['write_time'] = fields.Datetime.now()
        vals['user_id'] = self._uid

        return super(PackingOrder, self).create(vals)


class StockMove(models.Model):
    _inherit = "stock.move"

    packing_order_id = fields.Many2one('stock.packing.order',
                                        "Packing Order")
