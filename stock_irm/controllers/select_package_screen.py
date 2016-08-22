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


class SelectPackageController(http.Controller):
    @http.route('/select_package', type='http', auth='user')
    def select_package(self, **kw):
        env = http.request.env
        current_user = env['res.users'].browse(http.request.uid)

        return http.request.render('stock_irm.select_package_screen', {
            'status': 'ok',
            'user_name': current_user.partner_id.name,
            'worklocation_name': current_user.work_location_id.name,
            'worklocation_id': current_user.work_location_id.id or 0,
            'title': 'Select Package',
        })

    @http.route('/select_package/get_package', type='json', auth='user')
    def get_package(self, barcode, **kw):
        env = http.request.env

        # retrieve package information (product, quantity,...)
        scanned_package = env['stock.quant.package'].search(
            [('barcode', '=', str(barcode))]
        )

        if not scanned_package:
            return{
                'status': 'error',
                'error': 'Error',
                'message': 'Package could not be found',
            }

        if not scanned_package.quant_ids:
            return{
                'status': 'error',
                'error': 'Error',
                'message': 'Package has no move',
            }

        if not len(scanned_package.quant_ids) == 1:
            return {
                'status': 'error',
                'error': 'Error',
                'message': 'Package contains items from different move.',
            }

        quant = scanned_package.quant_ids
        picking = quant.reservation_id.picking_id
        if not picking:
            return {
                'status': 'error',
                'error': 'Error',
                'message': 'No picking is related to this package.',
            }
        current_location = env['stock.picking.type'].search(
            [('is_band_up_to_bo_cart', '=', True)], limit=1)
        if scanned_package.location_id != current_location.default_location_src_id:
            return {
                'status': 'error',
                'error': 'Error',
                'message': 'The package is not in your location',
            }

        product = scanned_package.quant_ids.product_id

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
                'description': product.description or 'No description',
                'quantity': total_qty,
                'image': '/web/binary/image?model=product.product&id=%s&field=image' % product.id,
            }
        }

    @http.route('/select_package/get_carts', auth='user', type='json')
    def get_carts(self):
        env = http.request.env
        current_location = env['stock.picking.type'].search(
            [('is_band_up_to_bo_cart', '=', True)], limit=1)
        # TODO: find all the cart with the current location as "parent location"
