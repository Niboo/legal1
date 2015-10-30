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
                supplier_product = [x for x in self.product_id.seller_ids if x.name == self.picking_id.partner_id]
                if self.location_dest_id:
                    ctx.update({
                        'location_dest_name': self.location_dest_id.name,
                        'location_is_temp_location': self.env.ref('putaway_apply.default_temp_location') == self.location_dest_id,
                    })
                if supplier_product:
                    ctx.update({
                        'supplier_product_code': supplier_product[0].product_code,
                        'procurement_group_name': supplier_product[0].procurement_group and supplier_product[0].procurement_group.name or '',
                    })
                product_ids = [self.product_id.id] * abs(qty)
                self.pool['product.product'].action_print_product_barcode(self._cr, self._uid, product_ids, context=ctx)
        return super(stock_pack_operation, self).write(values)

    @api.model
    def create(self, values):
        me = super(stock_pack_operation, self).create(values)
        if values.get('qty_done',False):
            qty = int(values.get('qty_done'))
            ctx = self._context.copy()
            supplier_product = [x for x in me.product_id.seller_ids if x.name == me.picking_id.partner_id]
            location_dest_id = values.get('location_dest_id',False)
            if location_dest_id:
                ctx.update({
                    'location_dest_name': self.env['stock.location'].browse(location_dest_id)['name'],
                    'location_is_temp_location': self.env.ref('putaway_apply.default_temp_location').id == location_dest_id,
                })
            if supplier_product:
                ctx.update({
                    'supplier_product_code': supplier_product[0].product_code,
                    'procurement_group_name': supplier_product[0].procurement_group and supplier_product[0].procurement_group.name or '',
                })
            product_ids = [me.product_id.id] * abs(qty)
            self.pool['product.product'].action_print_product_barcode(self._cr, self._uid, product_ids, context=ctx)
        return me


class stock_quant(models.Model):
    _inherit = 'stock.quant'

    def print_product_label(self, cr, uid, ids, context=None):
        ctx = context.copy()
        rec = self.browse(cr, uid, ids, context=context)
        product_ids = [rec.product_id.id] * abs(int(rec.qty))
        ctx.update({
            'location_dest_name': rec.location_id.name,
            # We can't figure out the procurement group from here, so just pretend it's not the temp location, even if it is.
            'location_is_temp_location': False,
        })

        self.pool['product.product'].action_print_product_barcode(cr, uid, product_ids, context=ctx)


class product_product(models.Model):
    _inherit = "product.product"

    def action_print_product_barcode(self, cr, uid, ids, context=None):
        report_name = 'xx_product_label.report_product_barcode'
        try:
            self.pool['report'].print_document(cr, uid, ids, report_name, context=context)
        except:
            pass
        return True
