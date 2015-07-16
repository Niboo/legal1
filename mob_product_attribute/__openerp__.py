 # -*- coding: utf-8 -*-
##############################################################################
#       
#    Odoo, Open Source Management Solution
#    Copyright (C) 2013 webkul
#    Author :
#               www.webkul.com  
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
