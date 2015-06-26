# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Bubbles-iT (<http://www.bubbles-it.be>)
#    Copyright (C) 2004 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
{
    "name" : "Report Delivery Extended",
    "version" : "0.1",
    "author": "Bubbles-iT.",
    "category": 'Warehouse Management',
    "description":'This module will add a delivery slip.',
    "website": "http://www.bubbles-it.be",
    "depends" : ["stock","sale_stock","base_report_to_printer","delivery",],
    "data": [
              'views/layouts_stockpicking.xml',
              "report_view.xml",
              "views/report_stockpicking.xml",
             ],
    "auto_install": True,
    "installable": True
}
