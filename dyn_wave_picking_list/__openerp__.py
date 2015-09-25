# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Dynapps <http://www.dynapps.be>
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
    'name': 'Wave Picking List',
    'version': '8.0.1.0.0',
    'category': 'Uncategorised',
    'description': """
This module adds a report on wave pickings, ordered by physical location
instead of grouping per picking, so that multiple pickings can efficiently
be picked in one run.
    """,
    'author': 'Dynapps',
    'website': 'http://www.dynapps.be',
    'license': 'AGPL-3',
    'depends': [
        'stock_picking_wave'
    ],
    'data': [
        'views/stock_picking_wave.xml',
        'report/report_picking_wave.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'images': [],
    'css': [],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
