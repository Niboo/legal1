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


class InboundController(http.Controller):
    @http.route('/picking_waves', type='http', auth="user")
    def picking_waves(self, **kw):
        current_user = http.request.env['res.users'].browse(http.request.uid)

        return http.request.render('stock_irm.picking_waves', {
            'user_name': current_user.partner_id.name,
            'worklocation_name': current_user.work_location_id.name,
            'title': 'Picking Waves',
        })

    @http.route('/picking_waves/get_waves', type='json', auth="user")
    def get_waves(self, **kw):
        env = http.request.env

        wave_list = []
        waves = env['stock.picking.wave'].search([
            ('user_id', '=', http.request.uid),
            ('state', '=', 'in_progress'),
        ])

        for wave in waves:
            if wave.picking_ids:

                wave_list.append({
                    'name': wave.name,
                    'id': wave.id,
                })

        results = {'status': 'ok',
                   'waves': wave_list,
                   }
        return results

    @http.route('/picking_waves/get_wave', type='json', auth="user")
    def get_wave(self, wave_id, **kw):
        env = http.request.env

        selected_wave = env['stock.picking.wave'].browse(int(wave_id))

        stock_move_ids = env['stock.move'].search([
            ('picking_id.wave_id', '=', selected_wave.id),
        ])

        picking_list = []

        for picking in selected_wave.picking_ids:
            progress = 100/len(picking.move_lines) *\
                       len(picking.move_lines.filtered(
                           lambda r: r.state == 'done')
                       )

            picking_list.append({
                'picking_id': picking.id,
                'progress_done': progress,
                'picking_name': picking.name,
            })

        # sort the location by alphabetical name
        move_list = []
        if not stock_move_ids:
            return {'status': 'empty'}

        for move in sorted(stock_move_ids,
                           key=lambda x: (x.location_dest_id.name,
                                          x.product_id.id)):
            if move.state == "assigned":

                move_list.append(
                    {'picking_id': move.picking_id.id,
                     'move_id': move.id,
                     'product': {
                         'picking_name': move.picking_id.name,
                         'product_id': move.product_id.id,
                         'product_name': move.product_id.name,
                         'product_description': move.product_id.description,
                         'product_quantity': move.product_uom_qty,
                         'product_image':
                         "/web/binary/image?model=product.product&id=%s&field=image"
                         % move.product_id.id,
                         'ean13': move.product_id.ean13,
                         'location_id': move.location_id.id,
                         'location_name': move.location_id.name,
                         'location_dest_name': move.location_dest_id.name,
                     },
                     'location_barcode': move.location_id.loc_barcode,
                     'location_dest_id': move.location_dest_id.id,
                     'location_dest_name': move.location_dest_id.name,
                     'location_dest_barcode': move.location_dest_id.loc_barcode
                     })

        results = {'status': 'ok', 'move_list': move_list,
                   'picking_list': picking_list, 'wave_id': selected_wave.id,
                   'wave_name': selected_wave.name
                   }
        return results

    @http.route('/picking_waves/create_picking', type='json', auth="user")
    def create_picking(self, **kw):
        env = http.request.env

        # retrieve the picking type we want to search (stock -> client)
        picking_type_ids = env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('active', '=', True)
        ])

        # retrieve the pickings with that type
        picking_ids = env['stock.picking'].search([
            ('picking_type_id', 'in', picking_type_ids.ids),
            ('state', '=', 'assigned'),
            ('wave_id', '=', False)
        ], limit=15)

        if not picking_ids:
            return {'status': 'empty'}

        # create a wave and attach the pickings we found
        wave = env['stock.picking.wave'].create({
            'user_id': http.request.uid,
        })
        #
        wave.picking_ids = picking_ids

        # search the stock moves related to those pickings,
        stock_move_ids = env['stock.move'].search([
            ('picking_id', 'in', wave.picking_ids.ids),
        ])

        picking_list = []

        for picking in picking_ids:
            progress = 100/len(picking.move_lines) *\
                       len(picking.move_lines.filtered(
                           lambda r: r.state == 'done')
                       )

            picking_list.append({
                'picking_id': picking.id,
                'progress_done': progress,
                'picking_name': picking.name,
            })

        # sort the location by alphabetical name
        move_list = []
        if not stock_move_ids:
            return {'status': 'empty'}

        for move in sorted(stock_move_ids,
                           key=lambda x: (x.location_dest_id.name,
                                          x.product_id.id)):
            if move.state == "assigned":

                move_list.append(
                    {'picking_id': move.picking_id.id,
                     'move_id': move.id,
                     'product': {
                         'picking_name' : move.picking_id.name,
                         'product_id': move.product_id.id,
                         'product_name': move.product_id.name,
                         'product_description': move.product_id.description,
                         'product_quantity': move.product_uom_qty,
                         'product_image':
                         "/web/binary/image?model=product.product&id=%s&field=image"
                         % move.product_id.id,
                         'ean13': move.product_id.ean13,
                         'location_id': move.location_id.id,
                         'location_name': move.location_id.name,
                         'location_dest_name': move.location_dest_id.name,
                     },
                     'location_barcode': move.location_id.loc_barcode,
                     'location_dest_id': move.location_dest_id.id,
                     'location_dest_name': move.location_dest_id.name,
                     'location_dest_barcode': move.location_dest_id.loc_barcode
                     })

        wave.confirm_picking()
        results = {'status': 'ok', 'move_list': move_list,
                   'picking_list': picking_list, 'wave_id': wave.id,
                   'wave_name': wave.name
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
    def validate_wave(self, wave_id, time_to_complete, **kw):
        env = http.request.env
        wave = env['stock.picking.wave'].browse(int(wave_id))

        wave.time_to_complete = time_to_complete

        for picking in wave.picking_ids:
            if any(move.state != 'done' for move in picking.move_lines):
                # if any move is not done, this picking can't
                # be confirmed with this wave.
                picking.wave_id = False

        wave.done()

        results = {
            "status": "ok",
        }
        return results

    @http.route('/picking_waves/current_user_waves', type='json', auth='user')
    def current_user_waves(self, **kw):
        env = http.request.env
        waves = env['stock.picking.wave'].search([
            ('state', '=', 'in_progress'),
            ('user_id', '=', http.request.uid)
        ])

        wave_list = []
        for wave in waves:
            if wave.picking_ids:
                wave_list.append({
                    'id': wave.id,
                    'name': wave.name,
                })

        results = {'status': 'ok',
                   'waves': wave_list}
        return results
