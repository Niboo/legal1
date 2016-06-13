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

class StockIndex(http.Controller):

    @http.route('/stock_index', type='http', auth="user")
    def stock_index(self, **kw):
        current_user = http.request.env['res.users'].browse(http.request.uid)

        return http.request.render('stock_irm.inbound_screen', {
            'user_name': current_user.partner_id.name,
            'worklocation_name': current_user.work_location_id.name,
            'worklocation_id': current_user.work_location_id.id or 0,
            'title': 'Index',
        })

    @http.route('/index/get_credentials', type='json', auth="user")
    def get_credentials(self, **kw):
        env = http.request.env
        current_user = env['res.users'].browse(http.request.uid)

        is_wh_manager = current_user.id in env.ref('stock.group_stock_manager').users.ids
        is_wh_user = current_user.id in env.ref('stock.group_stock_user').users.ids

        results = {'is_wh_manager': is_wh_manager,
                   'is_wh_user': is_wh_user,
                   'status':'ok'}
        return results
