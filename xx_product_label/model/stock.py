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
import re
import logging
from openerp import models, api


class stock_pack_operation(models.Model):
    _inherit = "stock.pack.operation"

    @api.multi
    def satisfies_unpacked_move(self, first=True):
        """ Return the until now unpacked move that the next increment of this
        pack will satisfy """
        qty = self.qty_done
        for link in self.linked_move_operation_ids:
            if not qty:
                return link.move_id
            if qty < link.qty:
                return False if first else link.move_id
            qty -= link.qty
        return False

    @api.multi
    def satisfies_unpacked_delivery(self):
        """ Return the until now unpacked incoming delivery that the next
        increment of this pack will satisfy """
        self.ensure_one()
        if (not self.location_dest_id or
                self.picking_id.picking_type_id.code != 'incoming'):
            return False
        move = self.satisfies_unpacked_move()
        if not move:
            return False
        picking_out = move.procurement_id.move_dest_id.picking_id
        if not picking_out:
            return False
        if any(move.state in ('done', 'assigned')
                for move in picking_out.move_lines):
            return False
        pack_moves = self.env['stock.move'].search(
            [('procurement_id.move_dest_id.picking_id', '=', picking_out.id)])
        for move in pack_moves:
            for operation in self.search(
                    [('linked_move_operation_ids.move_id', '=', move.id)]):
                if operation.satisfies_unpacked_move() != move:
                    return False
        return picking_out

    @api.one
    def write(self, values):
        """ Print the label of the packed product. If this is the first
        packing of a picking to a temporary location, print the picking as well

        Because the putaway strategy has not yet been applied at the moment of
        scanning, we look ahead in the configured putaway strategies to
        determine if this product will be going to the temp location.

        Set a destination on the label. This will either be the procurement
        group number (cq. the sales order reference), or the putaway as
        defined on the product.
        """
        if 'qty_done' in values:
            if values.get('qty_done') > self.qty_done:
                qty = int(values.get('qty_done') - self.qty_done)
                ctx = self._context.copy()
                supplier_product = [x for x in self.product_id.seller_ids if x.name == self.picking_id.partner_id]
                putaway_location = self.product_id.get_putaway_location()
                import pdb
                pdb.set_trace()
                is_temp_location = putaway_location == self.env.ref(
                    'putaway_apply.default_temp_location')
                if is_temp_location:
                    picking = self.satisfies_unpacked_delivery()
                else:
                    picking = False
                if picking:
                    # Printing can fail for a variety of reasons, e.g. if a
                    # product image is missing from the filesystem.
                    # Catch exceptions to prevent the interface from hanging
                    # in such a case.
                    try:
                        logging.getLogger(__name__).debug(
                            'Autoprinting picking #%s', picking.id)
                        self.env['report'].print_document(
                            picking,
                            'xx_report_delivery_extended.report_delivery_master')
                    except:
                        pass
                else:
                    # Just get the move's procurement group that this
                    # product will be packed for
                    move = self.satisfies_unpacked_move(first=False)
                    if move:
                        picking = move.picking_id
                destination = putaway_location.name
                if picking and picking.group_id.name:
                    # Strip off SO + year prefix to save space on the label
                    if re.match('(SO[0-9]{2})', picking.group_id.name):
                        destination = picking.group_id.name[4:]
                    else:
                        destination = picking.group_id.name
                ctx['destination'] = destination
                if supplier_product:
                    ctx['supplier_product_code'] = supplier_product[0].product_code
                product_ids = [self.product_id.id] * abs(qty)
                self.pool['product.product'].action_print_product_barcode(self._cr, self._uid, product_ids, context=ctx)
        return super(stock_pack_operation, self).write(values)


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
