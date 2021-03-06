# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Jerome Guerriat
#    Copyright 2015 Niboo SPRL
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import http
from datetime import datetime


class InboundController(http.Controller):
    @http.route('/picking_waves', type='http', auth="user")
    def picking_waves(self, **kw):
        current_user = http.request.env['res.users'].browse(http.request.uid)

        return http.request.render('stock_irm.picking_waves', {
            'user_name': current_user.partner_id.name,
            'worklocation_name': current_user.work_location_id.name,
            'title': 'Picking Waves',
            'user_email': current_user.partner_id.email,

        })

    @http.route('/outbound_wave/get_wave_template', type='json', auth='user')
    def get_wave_template(self, **kw):
        env = http.request.env

        wave_template_list = []

        wave_templates = env['wave.template'].search([
            ('wave_type', '=', 'outbound')])
        for wave_template in wave_templates:
            wave_template_list.append({
                'name': wave_template.label,
                'id': wave_template.id,
            })

        return {'status': 'ok',
                'wave_templates': wave_template_list}

    @http.route('/outbound_wave/get_outbound_wave', type='json', auth="user")
    def get_outbound_wave(self, wave_template_id, **kw):
        env = http.request.env
        current_user = env['res.users'].browse(http.request.uid)

        wave_list = []

        waves = env['picking.dispatch'].search([
            ('wave_template_id', '=', wave_template_id),
            ('state', '!=', 'done'),
            ('state', '!=', 'cancel'),
            '|', ('state', '!=', 'assigned'),
                 ('picker_id', '=', current_user.id),
            ('move_ids', '!=', False),
        ])

        for wave in waves:
            wave_list.append({
                'name': wave.name,
                'id': wave.id,
            })

        return {'status': 'ok',
                'waves': wave_list,
                }

    @http.route('/outbound_wave/get_wave', type='json', auth="user")
    def get_wave(self, wave_id, **kw):
        env = http.request.env
        current_user = env['res.users'].browse(http.request.uid)

        selected_wave = env['picking.dispatch'].browse(int(wave_id))
        # assign wave
        selected_wave['state'] = 'assigned'
        selected_wave['picker_id'] = current_user.id
        picking_list = self.create_picking_info(selected_wave.related_picking_ids)

        # sort the location by alphabetical name
        move_list = self.create_moves_info(selected_wave)

        return {
            'status': 'ok',
            'move_list': move_list,
            'picking_list': picking_list,
            'wave_id': selected_wave.id,
            'wave_name': selected_wave.name
        }

    @http.route('/outbound_wave/create_picking', type='json', auth="user")
    def create_picking(self, wave_template_id, selected_package_ids=[], **kw):
        env = http.request.env
        wave_template = env['wave.template'].browse(int(wave_template_id))

        outbound_wave = env['picking.dispatch'].create({
            'picker_id': http.request.uid,
            'state': 'draft',
            'wave_template_id': wave_template_id,
            'start_time': datetime.now()
        })

        if selected_package_ids:
            packages = env['stock.quant.package'].browse(selected_package_ids)
            for package in packages:
                move = package.quant_ids[0].reservation_id
                moves = self.find_counterpart_moves(move.picking_id)
                outbound_wave.move_ids += moves

        # retrieve the pickings with that type
        pickings = outbound_wave.related_picking_ids
        excluded_picking_ids = []
        for picking in pickings:
            picking.action_assign()

        picking_type = outbound_wave.picking_type_id
        cpt = 0
        max_pickings = wave_template.max_pickings_to_do

        while len(pickings) < max_pickings:
            # search for a confirmed picking
            picking = env['stock.picking'].search([
                ('picking_type_id', '=', picking_type.id),
                '|', '|', '|',
                ('state', '=', 'waiting'),
                ('state', '=', 'partially_available'),
                ('state', '=', 'confirmed'),
                # also take the "assigned" ones, since they may have been begon
                # in another wave
                ('state', '=', 'assigned'),
                ('move_lines.location_id', '=', picking_type.default_location_src_id.id),
                ('move_lines.dispatch_id', '=', False),
                ('id', 'not in', pickings.ids),
                ('id', 'not in', excluded_picking_ids)
            ], order='priority_weight DESC, id', limit=1, offset=cpt)


            procurement_group = picking.group_id
            proc_orders = env['procurement.order'].search(
                [('group_id', '=', procurement_group.id)])

            def get_ultimate_source():
                sources = set()
                for order in proc_orders:
                    if order.ultimate_source_procurement_id:
                        sources.add(order.ultimate_source_procurement_id)
                return sources

            sources_ids = [source.id for source in get_ultimate_source()]

            moves = env['stock.move'].search(
                [('procurement_id', 'in', sources_ids),
                 ('state', '!=', 'done')])

            if not picking:
                # if no more picking is found, then exit the loop
                break

            source_moves = env['stock.move'].search(
                [('procurement_id', 'in', sources_ids)])
            is_combined = False
            for move in source_moves:
                if move.picking_id.picking_type_id != picking.picking_type_id:
                    is_combined = True
                    break

            same_level_picking = picking.search(
                [('group_id', '=', picking.group_id.id),
                 ('state', '!=','done'),
                 ('picking_type_id', '=', picking.picking_type_id.id),
                 ('id', '!=', picking.id)])

            if is_combined and same_level_picking:
                excluded_picking_ids.append(picking.id)
                continue

            # check if the selected picking is fully available, assign and treat
            # it if its the case
            is_fully_available = True
            for move in moves:
                location = self.find_origin_location(move)
                qty_in_stock = self.get_location_qty(location,
                                                     move.product_id, True)

                if qty_in_stock < move.product_qty:
                    is_fully_available = False
                    break

            if not is_fully_available:
                excluded_picking_ids.append(picking.id)
                continue

            for move in moves:
                move.action_assign()

            for move in picking.move_lines:
                outbound_wave.move_ids += move
            pickings += picking

        if not pickings:
            outbound_wave.unlink()
            return {'status': 'empty'}

        picking_list = self.create_picking_info(pickings)
        move_list = self.create_moves_info(outbound_wave)

        if not move_list:
            return {'status': 'empty'}

        return {'status': 'ok',
                'move_list': move_list,
                'picking_list': picking_list,
                'wave_id': outbound_wave.id,
                'wave_name': outbound_wave.name
                }

    def get_location_qty(self, location, product, exclude_reservation=False):
        env = http.request.env

        domain = [('location_id', '=', location.id),
             ('product_id', '=', product.id)]

        if exclude_reservation:
            domain.append(('reservation_id', '=', False))

        quants = env['stock.quant'].search(domain)
        return sum([quant.qty for quant in quants])

    def transfer_package(self, move, package, cart_id):
        env = http.request.env

        picking = move.picking_id
        wizard_id = picking.do_enter_transfer_details()['res_id']
        wizard = env['stock.transfer_details'].browse(wizard_id)

        wizard.write({
            'item_ids': [(5, False, False)],
            'packop_ids': [(5, False, False)]
        })

        # then create a new wizard item
        wizard_values = {
            'package_id': package.id,
            'destinationloc_id': cart_id,
            'sourceloc_id': package.location_id.id,
        }

        wizard.write({
            'packop_ids': [(0, False, wizard_values)]
        })

        wizard.sudo().do_detailed_transfer()

    @http.route('/picking_waves/validate_move', type='json', auth="user")
    def validate_move(self, move_id, cart_id, box_barcode, **kw):
        env = http.request.env
        move = env['stock.move'].browse(int(move_id))
        dest_package = self.search_dest_package(box_barcode)

        counterparts_moves = self.find_counterpart_moves(move.picking_id)
        for counterpart_move in counterparts_moves:
            if counterpart_move.state != 'done':
                self.transfer_package(counterpart_move, dest_package, cart_id)


        self.transfer_move(move, cart_id, dest_package)
        picking = env['stock.picking'].browse(move.picking_id.id)

        percentage_complete = 100.0/len(picking.move_lines) \
                              * \
                              len(picking.move_lines.filtered(
                                  lambda r: r.state == 'done')
                              )

        results = {
            "status": "ok",
            "progress_done": percentage_complete,
            "picking_id": picking.id,
        }

        # if every move for this picking is "done", then the picking itself
        # is finished
        if not any(move.state != 'done' for move in picking.move_lines):
            results['finished_piking_id'] = picking.id

        return results

    @http.route('/picking_waves/validate_wave', type='json', auth="user")
    def validate_wave(self, wave_id, **kw):
        env = http.request.env
        wave = env['picking.dispatch'].browse(int(wave_id))

        for picking in wave.picking_ids:
            if any(move.state != 'done' for move in picking.move_lines):
                # if any move is not done, this picking can't
                # be confirmed with this wave.
                picking.wave_id = False

                # The location of the box should now be in the temp location
                new_loc = env['stock.location'].create({
                    'location_id':
                        env.ref('putaway_apply.default_temp_location').id,
                    'name': "%s - picking %s" % (picking.move_lines[0].location_dest_id.name, picking.id),
                })

                picking.move_lines[0].location_dest_id.location_id = new_loc

        return {
            "status": "ok",
        }

    def create_picking_info(self, pickings):
        picking_list = []
        for picking in pickings:
            picking_size = len(picking.move_lines.filtered(lambda r: r.state == 'done'))
            progress = 100 / len(picking.move_lines) * picking_size

            package = self.find_counterpart_package(picking)
            picking_list.append({
                'picking_id': picking.id,
                'progress_done': progress,
                'picking_name': picking.name,
                'box_barcode': package and package.barcode or False,
            })
        return picking_list

    def find_counterpart_moves(self, picking):
        env = http.request.env
        moves = env['stock.move'].search([('group_id','=',picking.group_id.id),
                                          ('picking_id.id','!=',picking.id),
                                          ('picking_type_id','=',picking.picking_type_id.id)])
        return moves

    def find_counterpart_package(self, picking):
        env = http.request.env
        domain = ['cancel', 'done']
        moves = env['stock.move'].search([('group_id','=',picking.group_id.id),
                                  ('picking_id.state', 'not in', domain)])

        for move in moves:
            if move.reserved_quant_ids \
                    and move.reserved_quant_ids[0].package_id:
                return move.reserved_quant_ids[0].package_id

    def find_origin_location(self, to_treat_move):
        env = http.request.env
        sub_locations = to_treat_move.location_id._get_sublocations()

        putaway_strategy = env['stock.product.putaway.strategy'].search([
            ('product_product_id', '=', to_treat_move.product_id.id),
            ('fixed_location_id.id', 'in', sub_locations)])
        return putaway_strategy.fixed_location_id or to_treat_move.location_id

    def create_moves_info(self, wave_id):
        stock_moves = wave_id.move_ids
        move_list = []

        def sort_by_origin_location(to_treat_move):
            return (self.find_origin_location(to_treat_move).name,
                    to_treat_move.product_id.id)

        sorted_moves = sorted(stock_moves, key=sort_by_origin_location)

        for move in sorted_moves:
            product_location = self.find_origin_location(move)
            if move.state == 'done':
                continue

            qty_available = self.get_location_qty(product_location,
                                                  move.product_id)
            move_list.append(
                {'picking_id': move.picking_id.id,
                 'picking_name': move.picking_id.name,
                 'move_id': move.id,
                 'product': {
                     'picking_name': move.picking_id.name,
                     'product_id': move.product_id.id,
                     'product_name': move.product_id.name,
                     'product_description': move.product_id.description or "No description",
                     'product_quantity': move.product_uom_qty,
                     'product_image':
                     "/web/binary/image?model=product.product&id=%s&field=image"
                     % move.product_id.id,
                     'ean13': move.product_id.default_code,
                     'location_id': product_location.id,
                     'location_name': product_location.name,
                     'qty_available': qty_available,
                 },
                 'location_dest_id': move.location_dest_id.id,
                 'location_dest_name': move.location_dest_id.name,
                 })

        return move_list

    @http.route('/outbound_wave/get_wave_time', type='json', auth='user')
    def get_wave_time(self, wave_id, **kw):
        env = http.request.env

        wave = env['picking.dispatch'].browse(int(wave_id))

        return {'status': 'ok',
                'total_time': wave.total_time}

    @http.route('/outbound_wave/get_carts', type='json', auth='user')
    def get_carts(self, wave_id, **kw):
        env = http.request.env
        outbound_wave = env['picking.dispatch'].browse(wave_id)
        destination = outbound_wave.picking_type_id.default_location_dest_id
        carts = []
        for cart in destination.child_ids:
            carts.append({
                'id': cart.id,
                'name': cart.name,
            })
        if not carts:
            return {'status': 'empty'}
        return {
            'status': 'ok',
            'carts': carts,
        }

    def transfer_move(self, move, cart_id, package):
        env = http.request.env
        picking = move.picking_id

        result = picking.do_enter_transfer_details()
        wizard_id = result['res_id']
        wizard = env['stock.transfer_details'].browse(wizard_id)
        destination = env['stock.location'].browse(cart_id)

        wizard.write({
            'item_ids': [(5, False, False)],
            'packop_ids': [(5, False, False)]
        })

        values = {
            'result_package_id': package.id,
            'product_id': move.product_id.id,
            'quantity': move.product_uom_qty,
            'sourceloc_id': move.location_id.id,
            'destinationloc_id': destination.id,
            'product_uom_id': move.product_id.uom_id.id
        }

        wizard.write({
            'item_ids': [(0, False, values)]
        })

        wizard.do_detailed_transfer()

    @http.route('/outbound_wave/check_package_empty', type='json',
                auth='user')
    def check_package_empty(self, barcode, **kwargs):
        env = http.request.env

        dest_package = env['stock.quant.package'].search([
            ('barcode', '=', str(barcode))
        ])

        if dest_package and (dest_package.quant_ids or
                                 dest_package.children_ids):
            return {'status': 'error'}

        return {'status': 'ok'}

    def search_dest_package(self, package_barcode):
        env = http.request.env

        dest_package = env['stock.quant.package'].search([
            ('barcode', '=', str(package_barcode))
        ])

        if not dest_package:
            dest_package = env['stock.quant.package'].create({
                'name': str(package_barcode),
                'barcode': str(package_barcode),
            })

        return dest_package

    @http.route('/outbound_wave/get_package', type='json', auth='user')
    def get_package(self, package_barcode, wave_template_id, **kw):
        env = http.request.env

        package = env['stock.quant.package'].search([
            ('barcode', '=', package_barcode)
        ])

        if package:
            return {
                'status': 'ok',
                'id': package.id,
                'name': package.name,
            }

        return {
            'status': 'error',
        }

    @http.route('/outbound_wave/cancel_move', type='json', auth='user')
    def cancel_move(self, move_id, **kw):
        env = http.request.env

        # remove the move from the dispatch wave and unreserve moves
        move = env['stock.move'].browse(move_id)
        wave_id = move.dispatch_id.id
        moves = move.picking_id.move_lines

        for move in moves:
            if move.state != 'done':
                move.reserved_quant_ids.quants_unreserve(move)
                move.dispatch_id = False

        return self.get_wave(wave_id)

    @http.route('/outbound_wave/get_stock_amount', type='json', auth='user')
    def get_stock_amount(self, product_id, location_id, **kw):
        env = http.request.env
        product = env['product.product'].browse(product_id)
        location = env['stock.location'].browse(location_id)

        qty_available = self.get_location_qty(location, product)

        return {
            'status': 'ok',
            'current_stock': qty_available,
        }

    @http.route('/outbound_wave/update_stock', type='json', auth='user')
    def update_stock(self, product_id, location_id, new_amount, **kw):
        env = http.request.env
        stock_change = env['stock.change.product.qty'].create({
            'product_id': product_id,
            'location_id': location_id,
            'new_quantity': new_amount,
        })
        stock_change.change_product_qty()

        product = env['product.product'].browse(product_id)
        location = env['stock.location'].browse(location_id)

        qty_available = self.get_location_qty(location, product)

        return {
            'status': 'ok',
            'new_quantity': qty_available,
        }
