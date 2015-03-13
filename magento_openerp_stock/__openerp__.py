 # -*- coding: utf-8 -*-
##############################################################################
#		
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 webkul
#	 Author :
#				www.webkul.com	
#
##############################################################################
{
    'name': 'Magento-OpenERP Stock Management',
    'version': '2.3.5',
    'category': 'Generic Modules',
    'sequence': 1,
    'summary': 'Manage Stock with MOB',
    'description': """	
    This Module helps in maintaining stock between openerp and magento with real time.
	
	NOTE : This module works very well with latest version of magento 1.9 and latest version of Odoo 8.0.
    """,
    'author': 'Webkul Software Pvt Ltd.',
    'depends': ['magento_bridge'],
    'website': 'http://www.webkul.com',
    'data': ['magento_openerp_stock_view.xml'],
    'installable': True,
    'active': False,
    #'certificate': '0084849360985',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
