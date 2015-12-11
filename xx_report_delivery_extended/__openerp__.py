# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
##############################################################################
{
    "name": "Report Delivery Extended",
    "version": "0.1",
    "description": 'This module will add a delivery slip.',
    "author": "DynApps",
    "category": "DynApps/Customizations",
    "website": "http://www.dynapps.be",
    "depends": [
        "sale_stock",
        "base_report_to_printer",
        "delivery",
        "dyn_wave_picking_list",
        "mob_multishop",
        "putaway_apply",
    ],
    "data": [
        'views/layouts_stockpicking.xml',
        "report_view.xml",
        "views/report_stockpicking.xml",
    ],
    "auto_install": True,
    "installable": True
}
