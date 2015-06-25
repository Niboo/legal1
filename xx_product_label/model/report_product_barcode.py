# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DynApps (<http://www.dynapps.be>). All Rights Reserved
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv
from openerp.report import report_sxw

class product_barcode(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(product_barcode, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {
            'get_supplier_product_code': self._get_supplier_product_code,
        })

    def _get_supplier_product_code(self):
        return self.localcontext.get('supplier_product_code', 'Unknown')

class report_product_barcode(osv.AbstractModel):
    _name = 'report.xx_product_label.report_product_barcode'
    _inherit = 'report.abstract_report'
    _template = 'xx_product_label.report_product_barcode'
    _wrapped_report_class = product_barcode
