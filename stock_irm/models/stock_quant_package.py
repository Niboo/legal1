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


class StockQuantPackage(models.Model):

    _inherit = "stock.quant.package"

    barcode = fields.Char("Barcode")
    picking_dispatch_id = fields.Many2one('picking.dispatch',
                                          'Picking Dispatch')

    _sql_constraints = [
        ('package_barcode_unique',
         'UNIQUE(barcode, location_id)',
         'The package barcode should be unique'),
    ]
