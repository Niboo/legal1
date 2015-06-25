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
                qty = int(values.get('qty_done') - self.qty_done)
                ctx = self._context.copy()
                supplier_product = [ x for x in self.product_id.seller_ids if x.name == self.picking_id.partner_id ]
                if supplier_product:
                    ctx.update({
                        'supplier_product_code': supplier_product[0].product_code,
                    })
                product_ids = []
                for x in xrange(qty):  # @UnusedVariable
                    product_ids.append(self.product_id.id)
                self.pool['product.product'].action_print_product_barcode(self._cr, self._uid, product_ids, context=ctx)
        return super(stock_pack_operation, self).write(values)

    @api.model
    def create(self, values):
        me = super(stock_pack_operation, self).create(values)
        if values.get('qty_done',False):
            qty = int(values.get('qty_done'))
            ctx = self._context.copy()
            supplier_product = [ x for x in me.product_id.seller_ids if x.name == me.picking_id.partner_id ]
            if supplier_product:
                ctx.update({
                    'supplier_product_code': supplier_product[0].product_code,
                })
            product_ids = []
            for x in xrange(qty):  # @UnusedVariable
                product_ids.append(me.product_id.id)
            self.pool['product.product'].action_print_product_barcode(self._cr, self._uid, product_ids, context=ctx)
        return me

class product_product(models.Model):
    _inherit = "product.product"

    def action_print_product_barcode(self, cr, uid, ids, context=None):
        report_name = 'xx_product_label.report_product_barcode'
        try:
            self.pool['report'].print_document(cr, uid, ids, report_name, context=context)
        except:
            pass
        return True
