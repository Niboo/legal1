##############################################################################
#
# Copyright (c) 2008-2012 NaN Projectes de Programari Lliure, S.L.
#                         http://www.NaN-tic.com
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

{
    "name" : "Jasper Reports",
    "version" : "0.1.1",
    "description" : "This module integrates Jasper Reports with OpenERP.",
    "author" : "NaN·tic",
    "website" : "http://www.nan-tic.com",
    "depends" : ["base","sale","account","stock","agaplan_terms_and_conditions","purchase"],
    "category" : "Generic Modules/Jasper Reports",
    "init_xml" : [],
    "demo_xml" : [ 
        'jasper_demo.xml' 
    ],
    "data" : [
        'wizard/jasper_create_data_template.xml',
        'jasper_wizard.xml',
        'report_xml_view.xml',
        'view/res_company.xml',
        'view/res_partner.xml',
        'view/xx_document_layout.xml',
        'view/xx_partner_document_layout.xml',
        'security/ir.model.access.csv',
        'data/jasper_reports_data.xml',
    ],
    "active": False,
    "installable": True
}

