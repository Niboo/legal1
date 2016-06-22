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


class BandupController(http.Controller):
    @http.route('/bandup', type='http', auth="user")
    def bandup(self, **kw):
        # render the first template
        env = http.request.env
        current_user = env['res.users'].browse(http.request.uid)

        return http.request.render('stock_irm.bandup_screen', {
            'status': 'ok',
            'user_name': current_user.partner_id.name,
            'worklocation_name': current_user.work_location_id.name,
            'worklocation_id': current_user.work_location_id.id or 0,
        })

    @http.route('/bandup/get_package', type='json', auth="user")
    def get_package(self, barcode, **kw):
        env = http.request.env

        # retrieve package information (product, quantity,...)
        scanned_package = env['stock.quant.package'].search(
            [('barcode', '=', barcode)]
        )

        product = env['product.product'].browse(
            scanned_package.quant_ids[0]
        )

        total_qty = 0
        for quant in scanned_package.quant_ids:
            total_qty += quant.qty

        return {
            'status': 'ok',
            'scanned_package': {
                'id': scanned_package.id,
                'barcode': scanned_package.barcode,
                'name': scanned_package.name,
            },
            'product': {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'quantity': total_qty,
                'image': "/web/binary/image?model=product.product&id=%s&field=image" % product.id,
            }
        }

    @http.route('/bandup/get_location', type='json', auth="user")
    def get_location(self, barcode, **kw):
        env = http.request.env

        # retrieve the scanned location
        location = env['stock.location'].search(
            [('barcode', '=', barcode)]
        )

        if not location:
            return {
                'status': 'error',
                'message': "No location have been found with that barcode"
            }

        return {
            'location_id': location.id,
            'location_name': location.name,
        }

    @http.route('/bandup/transfer_package', type='json', auth="user")
    def transfer_package(self, package_id, new_location_id, **kw):
        # transfer the package
        env = http.request.env

        scanned_package = env['stock.quant.package'].browse(package_id)
        new_location = env['stock.location'].browse(new_location_id)

        # change the location of the package and of the moves
        scanned_package.location_id = new_location

        for quant in scanned_package.quant_ids:
            quant.location_id = new_location

        return{
            'status': 'ok'
        }
