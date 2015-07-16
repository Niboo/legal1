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
	'name':'MOB Multi Language Extension',
	'version': '1',
	'summary': 'Multi Language Extension',
	'author':'Webkul Software Pvt. Ltd',
	'description':"""
MOB Multi Language Extension
-------------------------
	
	It'll synchronize category, product language data.

Multi language will sync for below Fields:
------------------------------------------

	1. Category:  name will be multi Language.
	2. Product:  name, description, description_sale.

	""",
	'category': 'Generic Modules',
	'sequence': 1,
	'depends':[
				'magento_bridge'
			],
	'data':[	'security/ir.model.access.csv',
				'multi_language_view.xml'
			],
	'installable': True,
	'active': False,
}
