# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Jerome Guerriat
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


class InventoryUpdateController(http.Controller):

    @http.route('/inventory_update', type='http', auth="user")
    def inventory_update(self, **kw):
        env = http.request.env
        current_user = env['res.users'].browse(http.request.uid)

        return http.request.render('stock_irm.inventory_update_screen', {
            'status': 'ok',
            'user_name': current_user.partner_id.name,
            'worklocation_name': current_user.work_location_id.name,
            'worklocation_id': current_user.work_location_id.id or 0,
            'title': 'Inventory',
            'user_email': current_user.partner_id.email,
        })

    @http.route('/inventory_update/get_location', type='json', auth="user")
    def get_location(self, barcode, **kw):
        env = http.request.env

        # retrieve the scanned location
        location = env['stock.location'].search(
            [('loc_barcode', '=', barcode)]
        )

        if not location:
            return {
                'status': 'error',
                'message': "No location has been found with this barcode"
            }

        return {
            'status': 'ok',
            'location_id': location.id,
            'location_name': location.name,
        }

    @http.route('/inventory_update/get_product', type='json', auth='user')
    def get_product(self, barcode, **kw):
        env = http.request.env

        product = env['product.product'].search([
            ('default_code', '=', barcode)
        ])

        if not product:
            return {
                'status': 'error',
                'message': "No product has been found with this barcode"
            }

        return {
            'status': 'ok',
            'product': {
                'id': product.id,
                'name': product.name,
                'description': product.description or 'No description',
                'default_code': product.default_code,
                'barcodes': [product.ean13 or ''],
                'image': '/web/binary/image?model=product.product&id=%s&field=image' % product.id,
            }
        }

    @http.route('/inventory_update/update_product_quantity',
                type='json', auth='user')
    def update_product_quantity(self, location_id, product_id, quantity, **kw):
        env = http.request.env
        try:
            wizard = env['stock.change.product.qty'].create({
                'location_id': int(location_id),
                'product_id': int(product_id),
                'new_quantity': int(quantity)
            })

            wizard.change_product_qty()
            return {
                'status': 'ok'
            }

        except BaseException as e:
            return {'status': 'error',
                    'error': type(e).__name__,
                    'message': str(e)}
