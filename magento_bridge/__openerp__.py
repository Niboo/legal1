# -*- coding: utf-8 -*-
##############################################################################
#
#   OpenERP, Open Source Management Solution
#    Copyright (C) 2013 webkul
#	 Author :
#				www.webkul.com	
#
##############################################################################
{
    'name': 'Magento Odoo Bridge',
    'version': '2.3.5',
    'category': 'Generic Modules',
     'sequence': 1,
    'summary': 'Basic MOB',
    'description': """
Magento Odoo Bridge (MOB)
============================
This Brilliant Module will Connect Odoo with Magento and synchronise all of your category, product, customer
---------------------------------------------------------------------------------------------------------------
and existing sales order(Invoice, shipping).
--------------------------------------------

Some of the brilliant feature of the module:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

	1. synchronise all the catalog categories to Magento.
	
	2. synchronise all the catalog products to Magento.
	
	3. synchronise all the existing sales order(Invoice, shipping) to Magento.
	
	4. Update all the store customers to Magento.
	
	5. synchronise product inventory of catelog products.
	
This module works very well with latest version of magento 1.9 and latest version of Odoo 8.0.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """,
	'author': 'Webkul Software Pvt Ltd.',
	'website': 'http://www.webkul.com',
	'depends': [
				'sale',
				'stock',
				'account_accountant',
				'delivery',
			],
	'data': [	
				'security/bridge_security.xml',
				'security/ir.model.access.csv',
				'wizard/message_wizard_view.xml',
				'wizard/status_wizard_view.xml',
				'mob_sequence.xml',
				'mob_view.xml',
				'mob_data.xml',				
				],
	'installable': True,
	'auto_install': False,	
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
