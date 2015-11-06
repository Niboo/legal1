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
        """ Print the label of the packed product. If this is the first
        packing of a picking to a temporary location, print the picking as well

        Because the putaway strategy has not yet been applied at the moment of
        scanning, we look ahead in the configured putaway strategies to
        determine if this product will be going to the temp location.

        See putaway_apply/putaway_apply.py
        """
        if 'qty_done' in values:
            if values.get('qty_done') > self.qty_done:
                qty = int(values.get('qty_done') - self.qty_done)
                ctx = self._context.copy()
                supplier_product = [x for x in self.product_id.seller_ids if x.name == self.picking_id.partner_id]
                if self.location_dest_id:
                    is_temp_location = False
                    if self.picking_id.picking_type_id.code == 'incoming':
                        temp_location = self.env.ref('putaway_apply.default_temp_location')
                        strats_by_prod = self.env['stock.fixed.putaway.byprod.strat'].search(
                            [('product_id', '=', self.product_id.id)], limit=1)
                        if strats_by_prod:
                            is_temp_location = (
                                strats_by_prod.fixed_location_id == temp_location)
                        else:
                            categ = self.product_id.categ_id
                            categ_ids = [categ.id]
                            while categ.parent_id:
                                categ_ids.append(categ.parent_id.id)
                                categ = categ.parent_id
                            strats = self.env['stock.fixed.putaway.strat'].search(
                                [('category_id', 'in', categ_ids)], limit=1)
                            if strats:
                                is_temp_location = (
                                    strats.fixed_location_id == temp_location)
                            else:
                                is_temp_location = True
                        if is_temp_location and self.picking_id.group_id and not any(
                                self.picking_id.pack_operation_ids.mapped('qty_done')):
                            outgoing_picking_ids = self.picking_id.search(
                                [('group_id', '=', self.picking_id.group_id.id),
                                 ('picking_type_id.code', '=', 'outgoing')])
                            if outgoing_picking_ids:
                                try:
                                    self.env['report'].print_document(
                                        outgoing_picking_ids[0],
                                        'xx_report_delivery_extended.report_delivery_master')
                                except:
                                    raise
                    ctx.update({
                        'location_dest_name': self.location_dest_id.name,
                        'location_is_temp_location': is_temp_location,
                        'procurement_group_name': self.picking_id.group_id and self.picking_id.group_id.name or '',
                    })
                if supplier_product:
                    ctx.update({
                        'supplier_product_code': supplier_product[0].product_code,
                    })
                product_ids = [self.product_id.id] * abs(qty)
                self.pool['product.product'].action_print_product_barcode(self._cr, self._uid, product_ids, context=ctx)
        return super(stock_pack_operation, self).write(values)

    @api.model
    def create(self, values):
        # TODO: to be refactored for lookahead like the write method
        me = super(stock_pack_operation, self).create(values)
        if values.get('qty_done',False):
            qty = int(values.get('qty_done'))
            ctx = self._context.copy()
            supplier_product = [x for x in me.product_id.seller_ids if x.name == me.picking_id.partner_id]
            location_dest_id = values.get('location_dest_id',False)
            if location_dest_id:
                is_temp_location = location_dest_id == self.env.ref(
                    'putaway_apply.default_temp_location').id
                ctx.update({
                    'location_dest_name': self.env['stock.location'].browse(location_dest_id)['name'],
                    'location_is_temp_location': is_temp_location,
                    'procurement_group_name': me.picking_id.procurement_group and me.picking_id.procurement_group.name or '',
                })
            if supplier_product:
                ctx.update({
                    'supplier_product_code': supplier_product[0].product_code,
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
