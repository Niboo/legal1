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
