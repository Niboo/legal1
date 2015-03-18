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
	'name':'MOB Extra Image Extension',
	'version': '1',
	'summary': 'Extra Image Extension',
	'author':'Webkul Software Pvt. Ltd',
	'description':"""
MOB Extra Image Extension
-------------------------

	Add An Extra Image tab inside product view.
	It'll sync all Magento Product Images inside Odoo
	Product Extra images and Vice Versa.

	""",
	'category': 'Generic Modules',
	'sequence': 1,
	'depends':[
				'magento_bridge'
			],
	'data':[	'security/ir.model.access.csv',
				'mob_extra_image_view.xml'
			],
	'installable': True,
	'active': False,
}
