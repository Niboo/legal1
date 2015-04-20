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
	'name':'MOB Multi Shop Extension',
	'version': '1',
	'summary': 'Multi Shop Extension',
	'author':'Webkul Software Pvt. Ltd',
	'description':"""
MOB Multi Shop Extension
------------------------
	
	It'll synchronize store information from Magento to Odoo.

Multi Shop Features:
--------------------

	1. Added Magento Store in Sales order.
	2. Added Magento websites in Products
	3. customer-group as a pricelist.

	""",
	'category': 'Generic Modules',
	'sequence': 1,
	'depends':[
				'magento_bridge'
			],
	'data':[	
				# 'security/ir.model.access.csv',
				'multi_shop_view.xml'
			],
	'installable': True,
	'active': False,
}
