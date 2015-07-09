# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
##############################################################################
{
    "name" : "Report Delivery Extended",
    "version" : "0.1",
    "description":'This module will add a delivery slip.',
    "author": "DynApps",
    "category": "DynApps/Customizations",
    "website": "http://www.dynapps.be",
    "depends" : ["stock","sale_stock","base_report_to_printer","delivery",],
    "data": [
              'views/layouts_stockpicking.xml',
              "report_view.xml",
              "views/report_stockpicking.xml",
             ],
    "auto_install": True,
    "installable": True
}
