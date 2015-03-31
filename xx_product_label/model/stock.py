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
from openerp import models, api

class stock_pack_operation(models.Model):
    _inherit = "stock.pack.operation"
    
    @api.one
    def write(self, values):
        if 'qty_done' in values:
            if values.get('qty_done') > self.qty_done:
                self.product_id.action_print_product_barcode()
        return super(stock_pack_operation, self).write(values)

class product_product(models.Model):
    _inherit = "product.product"

    @api.one
    def action_print_product_barcode(self):
        report_name = 'xx_product_label.report_product_barcode'
        try:
            self.pool['report'].print_document(self._cr,self._uid,[self.id],report_name)
        except:
            pass
        return True