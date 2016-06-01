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
from openerp.exceptions import Warning


class StockPickingType(models.Model):

    _inherit = "stock.picking.type"

    is_for_picking_wave = fields.Boolean("Is in picking waves")

    is_receipts = fields.Boolean("Is Receipts")

    @api.multi
    @api.constrains('is_receipts')
    def _check_single_inbound_receipt(self):
        self.ensure_one()
        if len(self.env['stock.picking.type'].search(
                [('is_receipts', '=', True)])) > 1:
            raise Warning("You should not select multiple inbound screen"
                          " picking type")
