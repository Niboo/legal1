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
