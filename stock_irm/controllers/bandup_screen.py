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
            'title': 'Bandup',
        })

    @http.route('/bandup/get_package', type='json', auth="user")
    def get_package(self, barcode, **kw):
        env = http.request.env

        input_location = env.ref('stock.stock_location_company')

        # retrieve package information (product, quantity,...)
        scanned_package = env['stock.quant.package'].search(
            [('barcode', '=', str(barcode)),
             # ('location_id', 'in', input_location._get_sublocations())
             ]
        )

        if not scanned_package:
            return{
                "result": "error",
                "message": "Package couldnt be found",
            }

        product = scanned_package.quant_ids[0].product_id

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

    @http.route('/bandup/move_package', type='json', auth='user')
    def move_package(self, package_id, **kw):
        env = http.request.env

        package = env['stock.quant.package'].browse(package_id)
        self.transfer_package(package, False)

        return {
            'status': 'ok',
        }


    @http.route('/bandup/transfert_package_batch', type='json', auth="user")
    def transfert_package_batch(self, package_ids, **kw):
        env = http.request.env

        package_list = []

        # for each package
        for package_id in package_ids:
            package = env['stock.quant.package'].browse(package_id)
            package = self.transfer_package(package)

            total_qty = 0
            for quant in package.quant_ids:
                total_qty += quant.qty

            package_list.append({
                'product_name': package.quant_ids[0].product_id.name,
                'product_description': package.quant_ids[0].product_id.description,
                'product_quantity': total_qty,
                'location_name':"dummy for the moment",
                'package_barcode': package.barcode,
                'package_id': package.id,
                'location_dest_barcode': 'test',
                'product_image':
                     "/web/binary/image?model=product.product&id=%s&field=image"
                     % package.quant_ids[0].product_id.id,
            })

        return{
            'status': 'ok',
            'package_list': package_list,
        }

    def transfer_package(self, package, is_end_package_needed=True):
        env = http.request.env

        destination = False
        end_package = False

        for quant in package.quant_ids:
            picking = quant.reservation_id.picking_id

            result = picking.do_enter_transfer_details()
            wizard_id = result['res_id']
            my_wizard = env['stock.transfer_details'].browse(wizard_id)

            if not destination:
                item = my_wizard.item_ids.filtered(lambda r: r.package_id == package)
                packop = my_wizard.packop_ids.filtered(lambda r: r.package_id == package)

                destination = item and item.destinationloc_id or packop.destinationloc_id

                if is_end_package_needed:
                    end_package = self.search_dest_package(package.barcode, destination)

            my_wizard.write({
                'item_ids': [(5, False, False)],
                'packop_ids': [(5, False, False)]
            })

            wizard_values = {
                    'package_id': package.id,
                    'product_id': quant.product_id.id,
                    'quantity': quant.qty,
                    'sourceloc_id': quant.location_id.id,
                    'destinationloc_id': destination.id,
                    'product_uom_id': quant.product_id.uom_id.id
                }

            if is_end_package_needed:
                wizard_values['result_package_id'] = end_package.id,

            my_wizard.write({
                'item_ids': [(0, False, wizard_values)]
            })

            my_wizard.do_detailed_transfer()
        package.unlink()
        return end_package

    def search_dest_package(self, package_barcode, location):
        env = http.request.env

        dest_package = env['stock.quant.package'].search([
            ('barcode', '=', str(package_barcode)),
            ('location_id', '=', location.id)
        ])

        if not dest_package:
            dest_package = env['stock.quant.package'].create({
                'name': str(package_barcode),
                'barcode': str(package_barcode),
                'location_id': location.id,
            })

        return dest_package
