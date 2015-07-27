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
    'author': 'Webkul Developers',
	'website': 'http://www.webkul.com',
    'summary': 'Basic MOB',
    'description': """

Magento Odoo Bridge (MOB)
=========================

This Brilliant Module will Connect Odoo with Magento and synchronise Data. 
--------------------------------------------------------------------------


Some of the brilliant feature of the module:
--------------------------------------------

	1. synchronise all the catalog categories to Magento.
	
	2. synchronise all the catalog products to Magento.

	3. synchronise all the Attributes and Values.
	
	4. synchronise all the order(Invoice, shipping) Status to Magento.
	
	5. Import Magento Regions.
	
	6. synchronise inventory of catelog products.
	
This module works very well with latest version of magento 1.9.* and Odoo 8.0
------------------------------------------------------------------------------
    """,
	'depends': [
				'base_vat',
				'sale',
				'stock',
				'account_accountant',
				'delivery',
				'wk_base_partner_patch',
			],
	'data': [	
				'res_config_view.xml',
				'security/bridge_security.xml',
				'security/ir.model.access.csv',
				'wizard/message_wizard_view.xml',
				'wizard/status_wizard_view.xml',
				'wizard/synchronization_wizard_view.xml',
				'core_overrides_view.xml',
				'mob_view.xml',
				'data/mob_server_actions.xml',
				'data/mob_data.xml',
				'mob_sequence.xml',
				],
	'application': True,
	'installable': True,
	'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
