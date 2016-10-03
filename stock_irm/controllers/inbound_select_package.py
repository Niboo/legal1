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


class SelectPackageController(http.Controller):
    @http.route('/select_package', type='http', auth='user')
    def select_package(self, **kw):
        env = http.request.env
        current_user = env['res.users'].browse(http.request.uid)

        return http.request.render('stock_irm.inbound_select_package', {
            'status': 'ok',
            'user_name': current_user.partner_id.name,
            'worklocation_name': current_user.work_location_id.name,
            'worklocation_id': current_user.work_location_id.id or 0,
            'title': 'Inbound Select Package',
            'user_email': current_user.partner_id.email,
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
                'message': 'Package could not be found! '
                           '(Check if the package has a barcode)',
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

    @http.route('/select_package/move_to_cart', auth='user', type='json')
    def move_to_cart(self, package_id, cart_id, **kw):
        env = http.request.env

        package = env['stock.quant.package'].browse(package_id)

        quant = package.quant_ids[0]
        picking = quant.reservation_id.picking_id

        self.check_destination(picking, cart_id)

        wizard_id = picking.do_enter_transfer_details()['res_id']
        wizard = env['stock.transfer_details'].browse(wizard_id)

        line = {
            'package_id': package.id,
            'sourceloc_id': package.location_id.id,
            'destinationloc_id': int(cart_id),
        }

        wizard.write({
            'item_ids': [(5,0,0)],
            'packop_ids': [(5,0,0),(0, False, line)]
        })

        wizard.sudo().do_detailed_transfer()

        return {'status': 'ok'}

    def check_destination(self, picking, destination_id):
        dest_location = picking.picking_type_id.default_location_dest_id
        dest_locations_list = [dest_location.id]
        dest_locations_list.extend(dest_location._get_sublocations())

        if destination_id not in dest_locations_list:
            raise exceptions.Warning('The location selected is not a correct '
                                     'location for this move.')

    @http.route('/select_package/get_carts', auth='user', type='json')
    def get_carts(self):
        env = http.request.env
        picking_type = env['stock.picking.type'].search(
            [('is_band_up_to_bo_cart', '=', True)], limit=1)
        location = picking_type.default_location_dest_id
        cart_list = []

        carts = env['stock.location'].search(
            [('location_id', '=', location.id)])

        for cart in carts:
            cart_list.append({
                'name': cart.name,
                'id': cart.id,
            })

        return {'status': 'ok',
                'carts': cart_list,
                }
