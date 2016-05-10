# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Jérôme Guerriat
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

{
    'name': 'Stock Reservation by weight',
    'category': 'Category',
    'summary': 'Summary',
    'website': '',
    'version': '9.1.0',
    'description': """
This module does not reserve quantity when a procurement is ran with the schedulers.
It adds a weight on sale orders and pickings. Pickings should be processed in the weight order

        """,
    'author': 'Niboo',
    'depends': [
        'sale',
        'stock',
        'procurement',
    ],
    'data': [
        'views/sale_order.xml',
        'views/stock_picking.xml',
    ],
    'qweb': [
    ],
    'demo': [
    ],
    'css': [
    ],
    'installable': True,
    'application': True,
}
