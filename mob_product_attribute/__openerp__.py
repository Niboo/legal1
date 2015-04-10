# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
    'name': 'MOB Product Attribute',
    'version': '2.4',
    'category': 'Generic Modules',
    'sequence':5,
    'summary': 'MOB Attribute Extension',
    'description': """
MOB Product Attribute Extension
===============================

Some of the brilliant feature of this extension:
------------------------------------------------
    This Module helps in maintaining Product Attributes and it's Custom Options between Magento and Odoo.

brilliant feature of the module:
--------------------------------

    1. it'll Maintain Magento Product Attributes(except Configurable).
    
    2. Maintain all Product Custom Options.

    3. Options value will be managed for Magento Order(inside order line).

	
	NOTE : This module works very well with latest version of magento 1.9.* and Odoo v8.0
    """,
    'author': 'Webkul Software Pvt Ltd.',
    'depends': ['magento_bridge'],
    'website': 'http://www.webkul.com',
    'data': [  
                'security/ir.model.access.csv',
                'mob_product_attributes_view.xml',
               ],
    'installable': True,
    'active': False,
    #'certificate': '0084849360985',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
