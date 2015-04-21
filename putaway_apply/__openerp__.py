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
    "name" : "Putaway apply",
    "version" : "0.1",
    "author": "Bubbles-iT.",
    "category": 'Warehouse Management',
    "description":' Usually Putaway strategy works on categories matched to the product on Shipment. This module does it on Product level.',
    "website": "http://www.bubbles-it.be",
    "depends" : ["purchase", "stock"],
    "demo" : [
             ],
    "data": [
             "putaway_apply_view.xml",
             'security/ir.model.access.csv',
             ],
    "auto_install": False,
    "installable": True
}