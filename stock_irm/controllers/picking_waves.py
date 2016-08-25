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
        })

    @http.route('/outbound_wave/get_wave_template', type='json', auth='user')
    def get_wave_template(self, **kw):
        env = http.request.env

        wave_template_list = []

        wave_templates = env['wave.template'].search([
            ('wave_type', '=', 'outbound')])
        for wave_template in wave_templates:
            wave_template_list.append({
                'name': wave_template.name,
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
        print selected_wave.id, selected_wave.state, current_user.name
        picking_list = self.create_picking_info(selected_wave.related_picking_ids)

        # sort the location by alphabetical name
        move_list = self.create_moves_info(selected_wave)

        results = {'status': 'ok', 'move_list': move_list,
                   'picking_list': picking_list, 'wave_id': selected_wave.id,
                   'wave_name': selected_wave.name

                   }
        return results

    @http.route('/outbound_wave/create_picking', type='json', auth="user")
    def create_picking(self, wave_template_id, **kw):
        env = http.request.env

        inbound_wave = env['picking.dispatch'].create({
            'picker_id': http.request.uid,
            'state': 'draft',
            'wave_template_id': wave_template_id,
            'start_time': datetime.now()
        })

        # retrieve the pickings with that type
        pickings = []

        cpt = 0
        while len(pickings) < 15:
            # search for a confirmed picking
            picking = env['stock.picking'].search([
                ('picking_type_id', '=', inbound_wave.picking_type_id.id),
                '|', '|', '|',
                ('state', '=', 'waiting'),
                ('state', '=', 'partially_available'),
                ('state', '=', 'confirmed'),
                # also take the "assigned" ones, since they may have been begon
                # in another wave
                ('state', '=', 'assigned'),
            ], order='priority_weight DESC, id', limit=1, offset=cpt)
            cpt += 1

            if not picking:
                # if no more picking is found, then exit the loop
                break

            # check if the selected picking is fully available, assign and treat
            # it if its the case
            is_fully_available = True
            for move in picking.move_lines:
                if move.product_id.qty_available < move.product_qty:
                    is_fully_available = False

            if not is_fully_available:
                break

            for move in picking.move_lines:
                move.action_assign()
                inbound_wave.move_ids += move
            pickings.append(picking)

        if not pickings:
            inbound_wave.unlink()
            return {'status': 'empty'}

        picking_list = self.create_picking_info(pickings)
        move_list = self.create_moves_info(inbound_wave)

        if not move_list:
            return {'status': 'empty'}

        results = {'status': 'ok',
                   'move_list': move_list,
                   'picking_list': picking_list,
                   'wave_id': inbound_wave.id,
                   'wave_name': inbound_wave.name
                   }
        return results

    @http.route('/picking_waves/validate_move', type='json', auth="user")
    def validate_move(self, move_id, **kw):
        env = http.request.env
        move = env['stock.move'].browse(int(move_id))
        move.action_done()
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

        results = {
            "status": "ok",
        }
        return results

    def create_picking_info(self, pickings):
        picking_list = []
        for picking in pickings:
            picking_size = len(picking.move_lines.filtered(lambda r: r.state == 'done'))
            progress = 100 / len(picking.move_lines) * picking_size

            picking_list.append({
                'picking_id': picking.id,
                'progress_done': progress,
                'picking_name': picking.name,
            })
        return picking_list

    def create_moves_info(self, wave_id):
        stock_moves = wave_id.move_ids
        move_list = []
        env = http.request.env

        def find_origin_location(to_treat_move):
            parent_location = to_treat_move.location_id.location_id
            sub_locations = to_treat_move.location_id._get_sublocations()

            putaway_strategy = env['stock.product.putaway.strategy'].search([
                ('product_product_id', '=', to_treat_move.product_id.id),
                ('fixed_location_id.id', 'in', sub_locations)])
            return putaway_strategy.fixed_location_id or to_treat_move.location_id

        def sort_by_origin_location(to_treat_move):
            return (find_origin_location(to_treat_move).name,
                    to_treat_move.product_id.id)

        sorted_moves = sorted(stock_moves, key=sort_by_origin_location)

        for move in sorted_moves:
            product_location = find_origin_location(move)

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
                     'ean13': move.product_id.ean13,
                     'location_id': move.location_id.id,
                     'location_name': product_location.name,
                 },
                 'location_barcode': move.location_id.loc_barcode,
                 'location_dest_id': move.location_dest_id.id,
                 'location_dest_name': move.location_dest_id.name,
                 'location_dest_barcode': move.picking_id.name
                 })

        return move_list

    @http.route('/outbound_wave/get_wave_time', type='json', auth='user')
    def get_wave_time(self, wave_id, **kw):
        env = http.request.env

        wave = env['picking.dispatch'].browse(int(wave_id))

        return {'status': 'ok',
                'total_time': wave.total_time}
