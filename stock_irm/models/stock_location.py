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

from openerp import api, fields, models
from openerp.exceptions import Warning


class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_in_usage = fields.Boolean('Currently in usage', default=False)

    is_inbound_cart = fields.Boolean('Is an inbound cart', default=False)
    is_bandup_location = fields.Boolean('Is a Bandup Location', default=False)
    is_damaged_location = fields.Boolean('Is the Damaged Products Location', default=False)
