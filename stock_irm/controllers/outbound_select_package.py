# -​*- coding: utf-8 -*​-
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


class OutboundSelectPackageController(http.Controller):
    @http.route('/outbound_select_package', type='http', auth='user')
    def select_package(self, **kw):
        env = http.request.env
        current_user = env['res.users'].browse(http.request.uid)

        return http.request.render('stock_irm.outbound_select_package', {
            'status': 'ok',
            'user_name': current_user.partner_id.name,
            'worklocation_name': current_user.work_location_id.name,
            'worklocation_id': current_user.work_location_id.id or 0,
            'title': 'Outbound Select Package',
            'user_email': current_user.partner_id.email,

        })

    @http.route('/outbound_select_package/process_package', auth='user',
                type='json')
    def process_package(self, barcode):
        env = http.request.env

        unpack = False

        # cart = env['stock.location'].browse(cart_id)
        scanned_package = env['stock.quant.package'].search(
            [('barcode', '=', str(barcode))]
        )

        if not scanned_package:
            return {
                'status': 'error',
                'error': 'Error',
                'message': 'The scanned package could not be found.',
            }

        bo_cart_to_band_down = env['stock.picking.type'].search(
            [('is_bo_cart_to_band_down', '=', True)], limit=1)

        output_to_customer = env['stock.picking.type'].search(
            [('is_output_to_customer', '=', True)], limit=1)

        bo_cart_upstairs = bo_cart_to_band_down.default_location_src_id

        output_default_loc = output_to_customer.default_location_src_id

        current_location = scanned_package.location_id

        if current_location not in bo_cart_upstairs.child_ids\
                and current_location not in output_default_loc.child_ids\
                and current_location != output_default_loc\
                and current_location != bo_cart_upstairs:
            return {
                'status': 'error',
                'error': 'Error',
                'message': 'The scanned package should not be on banddown.',
            }

        if current_location in output_default_loc.child_ids \
                or current_location == output_default_loc:
            unpack = True

        quant = scanned_package.quant_ids[0]
        picking = quant.reservation_id.picking_id
        procurement_group = picking.group_id
        procurement_group._procurement_order_state()
        is_complete = procurement_group.is_sale_order_complete

        if picking.picking_type_id.id == output_to_customer.id:
            env['report'].print_document(
                picking, 'odw_report_delivery.report_delivery_master')

        wizard_id = picking.do_enter_transfer_details()['res_id']
        wizard = env['stock.transfer_details'].browse(wizard_id)
        destination = picking.location_dest_id

        wizard.write({
            'item_ids': [(5, False, False)],
            'packop_ids': [(5, False, False)]
        })

        # then create a new wizard item
        wizard_values = {
            'package_id': scanned_package.id,
            'destinationloc_id': destination.id,
            'sourceloc_id': scanned_package.location_id.id,
        }

        wizard.write({
            'packop_ids': [(0, False, wizard_values)]
        })

        wizard.sudo().do_detailed_transfer()

        if unpack:
            scanned_package.unpack()

        if is_complete and not unpack:
            scanned_package.auto_move_pack()

        return {'status': 'ok',
                'is_complete': is_complete}

    @http.route('/outbound_select_package/get_package_ids', auth='user', type='json')
    def get_package_ids(self, cart_id):
        env = http.request.env
        cart = env['stock.location'].browse(cart_id)
        package_ids = env['stock.quant.package'].search(
            [('location_id', '=', int(cart.id))]
        )

        if not package_ids:
            return {
                'status': 'error',
                'error': 'Error',
                'message': 'The cart does not contain any packages.',
            }

        package_list = []

        for package in package_ids:
            product = package.quant_ids[0].product_id
            quant = package.quant_ids[0]
            total_qty = 0
            for quant in package.quant_ids:
                total_qty += quant.qty

            package_list.append({
                'package': {
                    'id': package.id,
                    'barcode': package.barcode,
                    'name': package.name,
                },
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'description': product.description or 'No description',
                    'quantity': total_qty,
                    'image': '/web/binary/image?model=product.product&id=%s&field=image' % product.id,
                }
            })

        return {'status': 'ok',
                'package_ids': package_list,
                }
