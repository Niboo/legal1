# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 DynApps <http://www.dynapps.be>
#
#    @author Stefan Rijnhart <stefan.rijnhart@dynapps.be>
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
    'name': 'Track originating sale order lines from the purchase order',
    'version': '8.0.1.0.0',
    'depends': [
        'sale',
        'purchase',
    ],
    'data': [
        'views/procurement_order.xml',
        'views/purchase_order.xml',
        'views/purchase_order_line.xml',
        'views/procurement_group.xml',
    ],
    'author': 'DynApps',
    'category': 'DynApps/Customizations',
    'website': 'http://www.dynapps.be',
    'installable': True,
}
