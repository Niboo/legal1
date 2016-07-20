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
    'name': 'Inventory Responsive Management',
    'category': 'Category',
    'summary': 'Summary',
    'website': '',
    'version': '9.1.0',
    'description': """
Module
        """,
    'author': 'Niboo',
    'depends': [
        'xx_product_supplierinfo_tags',
        'dyn_report_to_printer_location',
        'base_report_to_printer',
        'stock',
        'procurement',
        'stock_weight_reservation',
        'stock_putaway_product',
        'picking_dispatch_multiwave',
    ],
    'data': [
        'views/res_partner.xml',
        'templates/layout.xml',
        'views/res_users.xml',
        'views/printing_printers.xml',
        'views/work_location.xml',
        'views/stock_location.xml',
        'views/stock_picking_type.xml',
        'views/stock_index_view.xml',
        'views/packing_order.xml',
        'views/inbound_damage_reason.xml',
        'data/sequence_packing.xml',
        'security/ir.model.access.csv',
        'views/stock_quant_package.xml',
        'views/inbound_wave.xml',
        'views/stock_incomplete_reason.xml',
        'views/picking_dispatch_view.xml',
        'data/staging_location.xml',
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
