# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Tobias Zehntner
#    Copyright 2016 Niboo SPRL
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
from openerp.http import request


class PrintController(http.Controller):
    @http.route('/print_wave', type='json', auth="user")
    def print_wave(self, wave_id, **kw):
        env = http.request.env
        current_wave = env['stock.picking.wave'].browse(wave_id)

        try:
            current_wave.print_wave()
            return {'status': 'ok'}
        except BaseException as e:
            return {'status': 'error',
                    'error' : type(e).__name__,
                    'message': str(e)}

    @http.route('/print_pickings', type='json', auth="user")
    def print_picking(self, wave_id, **kw):
        env = http.request.env
        current_wave = env['stock.picking.wave'].browse(wave_id)

        try:
            current_wave.print_picking()
            return {'status': 'ok'}
        except BaseException as e:
            return {'status': 'error',
                    'error' : type(e).__name__,
                    'message': str(e)}
