 # -*- coding: utf-8 -*-
##############################################################################
#		
#    Odoo, Open Source Management Solution
#    Copyright (C) 2013 webkul
#	 Author :
#				www.webkul.com	
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
