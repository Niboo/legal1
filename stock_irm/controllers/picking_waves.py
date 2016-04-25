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
from openerp import exceptions
from datetime import datetime
from openerp.http import request


class InboundController(http.Controller):
    @http.route('/picking_waves', type='http', auth="user")
    def picking_waves(self, **kw):
        current_user = http.request.env['res.users'].browse(http.request.uid)

        return http.request.render('stock_irm.picking_waves', {
            'user_name': current_user.partner_id.name,
            'worklocation_name': current_user.work_location_id.name,
        })

    @http.route('/picking_waves/create_picking', type='json', auth="user")
    def create_picking(self, **kw):
        env = http.request.env
        env['stock.picking.wave'].create(
            {'user_id': http.request.uid}
        )

        picking_type_ids = env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('active', '=', True)
        ]).ids

        pickings_ids = env['stock.picking'].search([
            ('picking_type_id', 'in', picking_type_ids),
            ('state', '=', 'waiting')
        ], limit=15).ids

        stock_move_ids = env['stock.move'].search([
            ('pickinh_id', 'in', pickings_ids)
        ])

        # stock_move_ids = sorted(line_list, key=itemgetter(0, 1, 2, 3))
