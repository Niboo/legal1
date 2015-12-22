# -*- coding: utf-8 -*-
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
import logging
import re
import time
from openerp import models, api, fields
from openerp.exceptions import Warning as UserError
from openerp.tools.translate import _


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    @api.depends('move_dest_id')
    def _get_move_ultimate_dest_id(self):
        """ Retrieve the ultimate destination move, if any. From any
        procuring move, this allows easy retrieval to a related MTO sale order,
        if any. """
        for move in self:
            dest = move.move_dest_id
            while dest.move_dest_id:
                dest = dest.move_dest_id
            move.move_ultimate_dest_id = dest

    move_ultimate_dest_id = fields.Many2one(
        'stock.move', store=True,
        string='Ultimate destination move',
        compute='_get_move_ultimate_dest_id')


class stock_pack_operation(models.Model):
    _inherit = "stock.pack.operation"

    @api.multi
    def satisfies_unpacked_move(self, qty, first=True):
        """ Return the until now unpacked move that the next increment of this
        pack will satisfy

        Param qty: the pack's qty_done plus the offset position of the products
        that are being iterated over. I.e. qty is base 0.
        """
        for link in self.linked_move_operation_ids:
            if not qty:
                return link.move_id
            if qty < link.qty:
                return False if first else link.move_id
            qty -= link.qty
        return False

    @api.multi
    def satisfies_unpacked_delivery(self, qty):
        """ Return the until now unpacked incoming delivery that the next
        increment of this pack will satisfy """
        self.ensure_one()
        if (not self.location_dest_id or
                self.picking_id.picking_type_id.code != 'incoming'):
            return False
        move = self.satisfies_unpacked_move(qty)
        if not move:
            return False
        picking_out = move.move_ultimate_dest_id.picking_id
        if not picking_out:
            return False
        if any(move.state in ('done', 'assigned')
                for move in picking_out.move_lines):
            return False
        pack_moves = self.env['stock.move'].search(
            [('move_ultimate_dest_id.picking_id', '=', picking_out.id)])
        for move in pack_moves:
            for operation in self.search(
                    [('linked_move_operation_ids.move_id', '=', move.id)]):
                if operation.satisfies_unpacked_move(qty) != move:
                    return False
        return picking_out

    @api.one
    def write(self, values):
        """ Print the label of the packed product. If the move can be linked
        to a picking that it has been ordered for, and this is the first move
        that is being packed for that picking, print the picking as well so as
        to create a new basket in the warehouse for the related sales order.

        On the product label, print any procurement order group that triggered
        this product's procurement as its destination. This
        should usually be the sales order number. Otherwise, print the product
        putaway location as the destination.

        Note that in both cases we are applying a lookahead into the future of
        the stock move.

        Because products are grouped first on the purchase order and later on
        the pack operation, we iterate over each discrete product to find out
        if it satisfies a certain move or picking.
        """
        if 'qty_done' in values:
            report = 'xx_report_delivery_extended.report_delivery_master'
            if values.get('qty_done') > self.qty_done:
                now = time.time()
                logger = logging.getLogger('openerp.addons.xx_product_label')
                putaway_location = self.product_id.get_putaway_location()
                ctx = {}
                supplier_product = [
                    x for x in self.product_id.seller_ids
                    if x.name == self.picking_id.partner_id]
                if supplier_product:
                    ctx['supplier_product_code'] = (
                        supplier_product[0].product_code)
                for qty in range(int(self.qty_done),
                                 int(values['qty_done'])):
                    picking = False
                    if putaway_location == self.env.ref(
                            'putaway_apply.default_temp_location'):
                        picking = self.satisfies_unpacked_delivery(qty)
                        if picking:
                            if picking.picking_type_id.code == 'outgoing':
                                # Printing can fail for a variety of reasons,
                                # e.g. if a product image is missing from the
                                # filesystem. Catch exceptions to prevent the
                                # interface from hanging in such a case.
                                try:
                                    delta = time.time() - now
                                    now = time.time()
                                    logger.debug(
                                        '(%ss) Autoprinting picking %s',
                                        delta, picking.name)
                                    self.env['report'].print_document(
                                        picking, report)
                                except:
                                    pass
                                delta = time.time() - now
                                now = time.time()
                                logger.debug('(%ss) Picking printed', delta)
                        else:
                            # Just get the move's procurement group that this
                            # product will be packed for
                            move = self.satisfies_unpacked_move(
                                qty, first=False)
                            if move:
                                picking = (move.move_ultimate_dest_id
                                           .picking_id)
                    destination = putaway_location.name
                    if picking and picking.group_id.name:
                        # Strip off SO + year prefix to save space on the
                        # label
                        if re.match('(SO[0-9]{2})', picking.group_id.name):
                            destination = picking.group_id.name[4:]
                        else:
                            destination = picking.group_id.name
                    ctx['destination'] = destination
                    delta = time.time() - now
                    now = time.time()
                    logger.debug(
                        '(%ss) Autoprinting product label ("%s")', delta, ctx)
                    self.product_id.with_context(
                        ctx).action_print_product_barcode()
                    delta = time.time() - now
                    now = time.time()
                    logger.debug('(%ss) Product label printed', delta)
        return super(stock_pack_operation, self).write(values)


class stock_quant(models.Model):
    _inherit = 'stock.quant'

    def print_product_label(self, cr, uid, ids, context=None):
        ctx = context.copy()
        rec = self.browse(cr, uid, ids, context=context)
        product_ids = [rec.product_id.id] * abs(int(rec.qty))
        ctx.update({
            'destination': rec.location_id.name,
        })

        self.pool['product.product'].action_print_product_barcode(
            cr, uid, product_ids, context=ctx)


class product_product(models.Model):
    _inherit = "product.product"

    def action_print_product_barcode(self, cr, uid, ids, context=None):
        report_name = 'xx_product_label.report_product_barcode'
        try:
            self.pool['report'].print_document(
                cr, uid, ids, report_name, context=context)


class Picking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def check_work_location(self):
        if (not self.env.user.work_location_id and
                self.env.user.reset_work_location):
            raise UserError(
                _('Please configure your work location before starting to '
                  'process stock operations.'))

    @api.multi
    def open_barcode_interface(self):
        self.check_work_location()
        return super(Picking, self).open_barcode_interface()


class PickingType(models.Model):
    _inherit = 'stock.picking.type'

    @api.multi
    def open_barcode_interface(self):
        self.env['stock.picking'].check_work_location()
        return super(PickingType, self).open_barcode_interface()
